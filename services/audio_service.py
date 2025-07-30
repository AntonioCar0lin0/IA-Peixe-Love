import os, uuid, wave
from dotenv import load_dotenv
from google import generativeai as genai

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

def _save_wav(path: str, pcm_data: bytes, rate: int = 24000):
    with wave.open(path, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)  # 16-bit
        wf.setframerate(rate)
        wf.writeframes(pcm_data)

def gerar_audio(texto: str, usuario_id: str) -> str:
    try:
        model = genai.GenerativeModel("gemini-2.5-flash-preview-tts")

        response = model.generate_content(
            contents=[texto],
            generation_config={
                "response_modalities": ["AUDIO"],
                # REMOVIDO: "response_mime_type": "audio/wav",
                # O erro indica que este campo não é válido para o GenerateContentRequest
                # quando a modalidade é "AUDIO".
                "speech_config": {
                    "voice_config": {
                        "prebuilt_voice_config": {
                            "voice_name": "Puck"
                        }
                    }
                }
            }
        )

        # Verifique se a resposta realmente contém dados de áudio
        if response.parts and response.parts[0].inline_data and response.parts[0].inline_data.data:
            pcm_data = response.parts[0].inline_data.data
        else:
            print("[ERRO TTS Gemini]: Nenhuma parte de áudio encontrada na resposta.")
            return ""

        filename = f"audio_{usuario_id}_{uuid.uuid4()}.wav"
        path = os.path.join("static", filename)
        _save_wav(path, pcm_data)

        return f"/static/{filename}"

    except Exception as e:
        print(f"[ERRO TTS Gemini]: {e}")
        return ""