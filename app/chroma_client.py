"""
ChromaDB Client Modul
=====================
Initialisiert und verwaltet die Verbindung zur ChromaDB Vektordatenbank
mit Token-basierter Authentifizierung.

Funktionen:
- get_collection(): Gibt eine Collection aus ChromaDB zurück oder erstellt sie
"""

import chromadb
from .config import settings

# Verbindung zu ChromaDB mit Token-Authentifizierung
client = chromadb.HttpClient(
    host=settings.chroma_url,
    headers={settings.chroma_auth_token_transport_header: settings.chroma_auth_token}
)

def get_collection(name):
    """
    Gibt eine ChromaDB Collection zurück oder erstellt sie, falls sie nicht existiert.
    
    Args:
        name (str): Name der Collection (Format: "{tenant_id}_{scope}_{user_id}")
    
    Returns:
        chromadb.Collection: Die angeforderte Collection
    """
    return client.get_or_create_collection(name)
