import os
from .config import settings
from openai import OpenAI

IONOS_API_TOKEN = os.getenv("IONOS_API_KEY", settings.ionos_api_key)
IONOS_API_BASE_URL = os.getenv("IONOS_AI_BASE_URL", getattr(settings, "ionos_ai_base_url", "https://openai.inference.de-txl.ionos.com/v1"))
IONOS_MODEL = os.getenv("IONOS_MODEL", getattr(settings, "ionos_model", "BAAI/bge-m3"))

openai = OpenAI(
    api_key=IONOS_API_TOKEN,
    base_url=IONOS_API_BASE_URL
)

def embed_text(text):
    try:
        embedding = openai.embeddings.create(
            input=[text],
            model=IONOS_MODEL,
            encoding_format='float'
        )
        return embedding.data[0].embedding
    except Exception as e:
        raise RuntimeError(f"IONOS AI API Fehler: {e}")
