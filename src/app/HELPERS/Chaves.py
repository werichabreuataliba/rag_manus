
import os
from dotenv import load_dotenv
load_dotenv("config.env")

groq_api_key = os.getenv("LLM_ALURA")
manus_api_key = os.getenv("MANUS_API_KEY")
chave_secreta_manus = os.getenv('minha_chave_secreta')
usuario_rag_manus = os.getenv('usuario_rag_manus')
senha_manus = os.getenv('senha_manus')
PDF_PATH = os.getenv("PDF_PATH")
URL_MANUS_LIST=os.getenv("url_manus_list")
URL_MANUS_CREATE=os.getenv("url_manus_create")

if not groq_api_key or not manus_api_key:
    raise ValueError(
        "GROQ_API_KEY ou MANUS_API_KEY não encontrada."
    )

print("API Keys carregadas com sucesso.")