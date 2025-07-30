from supabase import create_client
from dotenv import load_dotenv
import os


load_dotenv()

SUPABASE_URL  = os.getenv("SUPABASE_URL")
SUPABASE_KEY  = os.getenv("SUPABASE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


def obter_entrada_nao_processada():
    """
    Busca o primeiro registro de 'conselhos' cuja resposta ainda é nula.
    """
    data = (
        supabase
        .table("conselhos")
        .select("*")
        .is_("resposta_texto", None)
        .limit(1)
        .execute()
    )
    return data.data[0] if data.data else None


def atualizar_resposta(id, resposta, audio_url, imagem_url=None):
    """
    Atualiza o registro com a resposta gerada e URLs de mídia.
    """
    supabase.table("conselhos").update({
        "resposta_texto": resposta,
        "audio_url"     : audio_url,
        "imagem_url"    : imagem_url,
    }).eq("id", id).execute()

# --------------------------------------------------
#  Função utilitária de upload para Storage
# --------------------------------------------------
def upload_arquivo_storage(
    bucket: str,
    filename: str,
    conteudo_bytes: bytes,
    content_type: str = "audio/wav",
) -> str:
    """
    Faz upload de um arquivo em bytes para o bucket indicado
    e retorna a URL pública.
    """
    supabase.storage.from_(bucket).upload(
        path=filename,
        file=conteudo_bytes,
        file_options={"content-type": content_type},
    )
    return supabase.storage.from_(bucket).get_public_url(filename)
