import openai
import uuid
import os
from dotenv import load_dotenv

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

def gerar_audio(texto: str, id: str) -> str:
    try:
        # Gera o áudio usando OpenAI
        response = openai.audio.speech.create(
            model="tts-1-hd",
            voice="onyx",
            input=texto
        )
        
        # Salva o conteúdo do áudio
        filename = f"static/audio_{str(id)}_{uuid.uuid4()}.mp3"
        with open(filename, "wb") as f:
            f.write(response.content)
        
        return f"/{filename}"
    except Exception as e:
        print(f"[ERRO AO GERAR ÁUDIO]: {e}")
        return ""
