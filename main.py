import os
import uuid
import wave
import io # Para lidar com dados em memória
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from supabase import create_client, Client
from google import generativeai as genai
from services.gemini_service import gerar_resposta  # Importando a função do gemini_service
from fastapi.middleware.cors import CORSMiddleware

# Carregar variáveis de ambiente do .env (para desenvolvimento local)
load_dotenv()

# --- Configurações Supabase ---
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
    raise ValueError("Variáveis de ambiente SUPABASE_URL e SUPABASE_SERVICE_KEY devem ser configuradas.")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

# --- Configurações Gemini TTS ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("Variável de ambiente GEMINI_API_KEY deve ser configurada.")
genai.configure(api_key=GEMINI_API_KEY)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Pydantic Model para a entrada da API ---
class EntradaTeste(BaseModel):
    usuario_id: str
    angustia: str

# --- Função utilitária de upload para Storage ---
def upload_arquivo_storage(
    bucket: str,
    filename: str,
    conteudo_bytes: bytes,
    contenttype: str = "audio/wav",
) -> str:
    """ Faz upload de um arquivo em bytes para o bucket indicado e retorna a URL pública. """
    try:
        supabase.storage.from_(bucket).upload(
            path=filename,
            file=conteudo_bytes,
            file_options={"content-type": contenttype},
        )
        print(f"Upload inicial bem-sucedido para: {filename}")
    except Exception as e:
        if "The resource already exists" in str(e):
            print(f"Arquivo {filename} já existe, tentando atualizar...")
            supabase.storage.from_(bucket).update(
                path=filename,
                file=conteudo_bytes,
                file_options={"content-type": contenttype},
            )
            print(f"Atualização bem-sucedida para: {filename}")
        else:
            print(f"Erro inesperado no upload_arquivo_storage: {e}")
            raise

    return supabase.storage.from_(bucket).get_public_url(filename)

# --- Função para gerar áudio com Gemini TTS e fazer upload (CORRIGIDA) ---
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
            print(f"Tamanho do pcm_data bruto do Gemini: {len(pcm_data)} bytes") # Para depuração
        else:
            print("[ERRO TTS Gemini]: Nenhuma parte de áudio encontrada na resposta.")
            return ""

        # --- MUDANÇA CRÍTICA AQUI: Adicionar cabeçalho WAV aos dados PCM brutos ---
        audio_buffer = io.BytesIO()
        with wave.open(audio_buffer, "wb") as wf:
            wf.setnchannels(1) # Mono
            wf.setsampwidth(2) # 16-bit (2 bytes por amostra)
            wf.setframerate(24000) # Taxa de amostragem (verifique a documentação do Gemini TTS para a taxa exata)
            wf.writeframes(pcm_data)
        
        # Obter os bytes do arquivo WAV completo do buffer
        audio_buffer.seek(0) # Voltar ao início do buffer
        wav_file_bytes = audio_buffer.read()
        print(f"Tamanho do arquivo WAV completo: {len(wav_file_bytes)} bytes") # Para depuração

        # Gerar um nome de arquivo único para o Supabase Storage
        filename = f"conselho_audio_{usuario_id}_{uuid.uuid4()}.wav"
        bucket_name = "audio-conselhos" # Nome do seu bucket no Supabase Storage

        # Chamar a função de upload para o Supabase Storage com os bytes do arquivo WAV completo
        public_audio_url = upload_arquivo_storage(
            bucket=bucket_name,
            filename=f"respostas/{filename}",
            conteudo_bytes=wav_file_bytes, # AGORA ENVIAMOS O ARQUIVO WAV COMPLETO
            contenttype="audio/wav"
        )

        return public_audio_url # RETORNA A URL PÚBLICA DO SUPABASE STORAGE

    except Exception as e:
        print(f"[ERRO TTS Gemini]: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao gerar ou fazer upload do áudio: {e}")

# --- Endpoint da API ---
@app.post("/testar-resposta")
async def testar_resposta_manual(payload: EntradaTeste):
    try:
        print("Angústia recebida:", payload.angustia)
        
        # Usando a função do gemini_service para gerar a resposta
        resposta_texto = gerar_resposta(payload.angustia)
        print("Resposta gerada:", resposta_texto)
        
        audio_url = gerar_audio(resposta_texto, payload.usuario_id)
        print("URL pública do áudio:", audio_url)
        
        return {
            "status": "ok",
            "resposta": resposta_texto,
            "audio_url": audio_url,  # Esta é a URL pública completa do Supabase Storage
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"Erro inesperado no endpoint /testar-resposta: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno do servidor: {e}")