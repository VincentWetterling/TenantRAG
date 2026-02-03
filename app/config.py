from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    ionos_api_key: str
    chroma_url: str
    database_url: str

    class Config:
        env_file = "../.env"

settings = Settings()
