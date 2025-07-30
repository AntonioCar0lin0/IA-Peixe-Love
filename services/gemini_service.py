import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-2.5-pro')
direcionamento = (
    "Suponha que você é um peixe do amor, que faz desconselhos amorosos. "
    "Você é sarcástico e utiliza de humor ácido para responder às angústias dos seus usuários, gerando humor. "
    "Responda em uma frase curta e muito engraçada: "
)

def gerar_resposta(mensagem: str) -> str:
    prompt = (
        direcionamento + mensagem
    )
    response = model.generate_content(prompt)
    return response.text.strip()
