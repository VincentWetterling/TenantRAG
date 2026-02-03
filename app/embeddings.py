"""
Embeddings Modul
================
Konvertiert Texte in numerische Vektoren mittels IONOS AI Embeddings API.
Diese Vektoren werden verwendet für semantische Suche in ChromaDB.

Die Verwendung: embed_text() -> gibt Float-Array zurück
"""

import os
from .config import settings
from openai import OpenAI

# IONOS AI Konfiguration
IONOS_API_TOKEN = os.getenv("IONOS_API_KEY", settings.ionos_api_key)
IONOS_API_BASE_URL = os.getenv("IONOS_AI_BASE_URL", settings.ionos_ai_base_url)
IONOS_MODEL = os.getenv("IONOS_MODEL", settings.ionos_model)

# OpenAI-kompatibler Client für IONOS AI
openai = OpenAI(
    api_key=IONOS_API_TOKEN,
    base_url=IONOS_API_BASE_URL
)

def embed_text(text):
    """
    Konvertiert einen Text in einen numerischen Vektor (Embedding).
    
    Args:
        text (str): Der Text, der embedded werden soll
    
    Returns:
        list: Float-Array der Embedding-Dimension (normalerweise 1024 für bge-m3)
    
    Raises:
        RuntimeError: Falls die IONOS API nicht erreichbar ist oder einen Fehler zurückgibt
    """
    try:
        embedding = openai.embeddings.create(
            input=[text],
            model=IONOS_MODEL,
            encoding_format='float'
        )
        return embedding.data[0].embedding
    except Exception as e:
        raise RuntimeError(f"IONOS AI API Fehler: {e}")
