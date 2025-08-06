import os, uuid, wave
from dotenv import load_dotenv
from google import generativeai as genai
from supabase import create_client, Client # Importar create_client e Client
import io # Para lidar com dados em memória

load_dotenv()

# --- Configurações Supabase (Certifique-se que estas ENV estão no Render.com) ---
SUPABASE_URL = os.getenv("SUPABASE_URL")
# Use SUPABASE_SERVICE_KEY para o backend, não SUPABASE_KEY se esta for a pública
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY") # Ou SUPABASE_KEY se você a configurou com a service_role key
supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# --- Função utilitária de upload para Storage (já fornecida por você) ---
def upload_arquivo_storage(
    bucket: str,
    filename: str,
    conteudo_bytes: bytes,
    contenttype: str = "audio/wav",
) -> str:
    """ Faz upload de um arquivo em bytes para o bucket indicado e retorna a URL pública. """
    try:
        supabase.storage.from_(bucket).upload( # Use from_ para evitar conflito com from
            path=filename,
            file=conteudo_bytes,
            file_options={"content-type": contenttype},
        )
        return supabase.storage.from_(bucket).get_public_url(filename)
    except Exception as e:
        # Se o arquivo já existe, tente atualizar (opcional, dependendo da sua lógica)
        if "The resource already exists" in str(e):
            supabase.storage.from_(bucket).update(
                path=filename,
                file=conteudo_bytes,
                file_options={"content-type": contenttype},
            )
            return supabase.storage.from_(bucket).get_public_url(filename)
        print(f"Erro no upload_arquivo_storage: {e}")
        return ""

# --- Função _save_wav (não será mais usada para salvar localmente, mas pode ser útil para depuração) ---
def _save_wav(path: str, pcm_data: bytes, rate: int = 24000):
    with wave.open(path, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2) # 16-bit
        wf.setframerate(rate)
        wf.writeframes(pcm_data)

# --- Função gerar_audio corrigida ---
def gerar_audio(texto: str, usuario_id: str) -> str:
    try:
        model = genai.GenerativeModel("gemini-2.5-flash-preview-tts")
        response = model.generate_content(
            contents=[texto],
            generation_config={
                "response_modalities": ["AUDIO"],
                "speech_config": {
                    "voice_config": {
                        "prebuilt_voice_config": {
                            "voice_name": "Puck"
                        }
                    }
                }
            }
        )

        if response.parts and response.parts[0].inline_data and response.parts[0].inline_data.data:
            pcm_data = response.parts[0].inline_data.data
        else:
            print("[ERRO TTS Gemini]: Nenhuma parte de áudio encontrada na resposta.")
            return ""

        # --- MUDANÇA CRÍTICA AQUI ---
        # Em vez de salvar localmente e retornar um caminho relativo,
        # vamos fazer o upload para o Supabase Storage e retornar a URL pública.

        filename = f"audio_{usuario_id}_{uuid.uuid4()}.wav" # Nome único para o arquivo no Storage
        bucket_name = "audios-conselhos" # Nome do seu bucket no Supabase Storage

        # Chamar a função de upload para o Supabase Storage
        public_audio_url = upload_arquivo_storage(
            bucket=bucket_name,
            filename=f"respostas/{filename}", # Opcional: criar uma subpasta 'respostas' no bucket
            conteudo_bytes=pcm_data,
            contenttype="audio/wav"
        )

        # Opcional: Se quiser salvar uma cópia local para depuração, mantenha a linha abaixo
        # _save_wav(os.path.join("static", filename), pcm_data)

        return public_audio_url # RETORNA A URL PÚBLICA DO SUPABASE STORAGE

    except Exception as e:
        print(f"[ERRO TTS Gemini]: {e}")
        return ""

# --- Exemplo de uso no seu endpoint /testar-resposta (no arquivo principal do Flask/FastAPI) ---
# Certifique-se de que o endpoint chama esta função e retorna o audio_url
# @app.post("/testar-resposta")
# def testar_resposta_manual(payload: EntradaTeste):
#     try:
#         resposta = gerar_resposta(payload.angustia)
#         audio_url = gerar_audio(resposta, payload.usuario_id) # Esta linha agora retorna a URL pública
#         return {
#             "status": "ok",
#             "resposta": resposta,
#             "audio_url": audio_url, # O frontend receberá a URL pública completa
#         }
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Erro ao processar: {e}")