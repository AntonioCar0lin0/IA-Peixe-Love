from supabase import create_client
import os
from dotenv import load_dotenv

load_dotenv()
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")
supabase = create_client(url, key)

def obter_entrada_nao_processada():
    data = supabase.table("conselhos").select("*").is_("resposta_texto", None).limit(1).execute()
    if data.data:
        return data.data[0]
    return None

def atualizar_resposta(id, resposta, audio_url, imagem_url):
    supabase.table("conselhos").update({
        "resposta_texto": resposta,
        "audio_url": audio_url,
        "imagem_url": imagem_url
    }).eq("id", id).execute()
