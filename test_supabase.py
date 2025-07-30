from supabase import create_client
import os
from dotenv import load_dotenv

load_dotenv()
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")
supabase = create_client(url, key)

def testar_conexao():
    try:
        resposta = supabase.table("conselhos").select("*").limit(1).execute()
        print("✅ Conectado ao Supabase!")
        print("📦 Resultado da tabela:", resposta.data)
    except Exception as e:
        print("❌ Erro ao conectar ou consultar:", e)

testar_conexao()
