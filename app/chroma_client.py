import chromadb
from .config import settings

client = chromadb.HttpClient(host=settings.chroma_url)

def get_collection(name):
    return client.get_or_create_collection(name)
