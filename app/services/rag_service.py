import numpy as np
from langchain_ollama import OllamaEmbeddings

from app.configs.app_settings import settings
from app.configs.llm_settings import LLM_EMBEDDING_MODEL


embeddings = OllamaEmbeddings(
    model=LLM_EMBEDDING_MODEL,
    base_url=settings.ollama_base_url,
)

class RAGService:

    @staticmethod
    def embed_text(text: str) -> np.ndarray:
        vector = embeddings.embed_query(text)
        return np.array(vector, dtype=np.float32)
