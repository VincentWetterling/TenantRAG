"""
Konfigurationsmodul für TenantRAG
=====================================
Lädt Umgebungsvariablen aus .env Datei und stellt sie als Settings-Objekt bereit.

Benötigte Umgebungsvariablen:
- IONOS_API_KEY: API-Schlüssel für IONOS AI Embeddings
- IONOS_AI_BASE_URL: Base URL für IONOS AI API
- IONOS_MODEL: Modellname für Embeddings
- CHROMA_URL: URL zu ChromaDB Server
- CHROMA_AUTH_TOKEN: Token für ChromaDB Authentifizierung
- DATABASE_URL: Verbindungsstring für MySQL/MariaDB
- WEBUI_USERNAME: Benutzername für Streamlit Dashboard (optional)
- WEBUI_PASSWORD: Passwort für Streamlit Dashboard (optional)
"""

from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """Hauptkonfigurationsklasse für die Anwendung"""
    
    # IONOS AI Embeddings
    ionos_api_key: str
    ionos_ai_base_url: str = "https://openai.inference.de-txl.ionos.com/v1"
    ionos_model: str = "BAAI/bge-m3"
    
    # ChromaDB Vektordatenbank
    chroma_url: str
    chroma_auth_provider: str = "token"
    chroma_auth_token: str
    chroma_auth_token_transport_header: str = "X-Token"
    
    # Relationale Datenbank
    database_url: str
    
    # Streamlit WebUI
    webui_username: str
    webui_password: str

    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()
