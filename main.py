from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from services.gemini_service import gerar_resposta
from services.audio_service import gerar_audio
#from services.image_service import obter_imagem
from services.supabase_client import obter_entrada_nao_processada, atualizar_resposta
from pydantic import BaseModel

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/processar-entrada")
def processar_entrada():
    try:
        entrada = obter_entrada_nao_processada()
        print("Entrada recebida do Supabase:", entrada)

        if not entrada:
            return {"status": "sem novas entradas"}
        #logs
        resposta = gerar_resposta(entrada["angustia"])
        print("Resposta gerada:", resposta)

        audio_url = gerar_audio(resposta, entrada["id"])
        print("Áudio salvo em:", audio_url)

        #imagem_url = obter_imagem()
        #print("Imagem salva em:", imagem_url)

        #if not audio_url or not imagem_url:
        #    raise HTTPException(status_code=500, detail="Erro ao gerar mídia.")

        atualizar_resposta(
            id=entrada["id"],
            resposta=resposta,
            audio_url=audio_url
            #imagem_url=imagem_url
        )

        return {
            "status": "ok",
            "mensagem": "Resposta processada",
            "resposta": resposta,
            "audio_url": audio_url
            #"imagem_url": imagem_url
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro interno: {e}")

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

        #imagem_url = obter_imagem()
        #print("Imagem salva em:", imagem_url)

        return {
            "status": "ok",
            "resposta": resposta,
            "audio_url": audio_url
            #"imagem_url": imagem_url
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao processar: {e}")