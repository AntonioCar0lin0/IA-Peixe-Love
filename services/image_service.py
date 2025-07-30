import google.generativeai as genai
from google.genai import types
import uuid
import os
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

def obter_imagem(prompt: str = "um peixe sarcástico do amor flutuando em um oceano rosa") -> str:
    model = genai.GenerativeModel("gemini-2.0-flash-preview-image-generation")

    response = model.generate_content(
        contents=prompt,
        generation_config=types.GenerationConfig(),  # vazio ou com outras configs
        response_mime_types=["image/png"]
    )

    for part in response.parts:
        if hasattr(part, "inline_data") and part.inline_data:
            image_data = part.inline_data.data
            filename = f"static/img_{uuid.uuid4()}.png"
            with open(filename, "wb") as f:
                f.write(image_data)
            return f"/{filename}"

    return "/static/peixe.png"

