from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from services.gemini_service import gerar_resposta
from services.audio_service import gerar_audio
from services.supabase_client import (
    obter_entrada_nao_processada,
    atualizar_resposta,
)

app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.mount("/static", StaticFiles(directory="static"), name="static")



@app.post("/processar-entrada")
def processar_entrada():
    try:
        entrada = obter_entrada_nao_processada()
        print("Entrada recebida do Supabase:", entrada)

        if not entrada:
            return {"status": "sem novas entradas"}

        # 1) Texto sarcástico
        resposta = gerar_resposta(entrada["angustia"])
        print("Resposta gerada:", resposta)

        # 2) Áudio PT-BR via Gemini TTS
        audio_url = gerar_audio(resposta, entrada["id"])
        print("Áudio salvo em:", audio_url)

        # 3) Atualiza registro
        atualizar_resposta(
            id=entrada["id"],
            resposta=resposta,
            audio_url=audio_url,
            imagem_url=None,          # não estamos gerando imagem agora
        )

        return {
            "status": "ok",
            "mensagem": "Resposta processada",
            "resposta": resposta,
            "audio_url": audio_url,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro interno: {e}")

# ---------- rota de teste -------------------------------

class EntradaTeste(BaseModel):
    usuario_id: str
    angustia: str

@app.post("/testar-resposta")
def testar_resposta_manual(payload: EntradaTeste):
    try:
        print("Angústia recebida:", payload.angustia)

        resposta = gerar_resposta(payload.angustia)
        print("Resposta gerada:", resposta)

        audio_url = gerar_audio(resposta, payload.usuario_id)
        print("Áudio salvo em:", audio_url)

        return {
            "status": "ok",
            "resposta": resposta,
            "audio_url": audio_url,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao processar: {e}")
