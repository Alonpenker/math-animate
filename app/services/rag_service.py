import numpy as np
from langchain_openai import OpenAIEmbeddings

from app.configs.app_settings import settings
from app.configs.llm_settings import LLM_EMBEDDING_MODEL, LLM_EMBEDDING_DIMENSIONS


embeddings = OpenAIEmbeddings(
    model=LLM_EMBEDDING_MODEL,
    dimensions=LLM_EMBEDDING_DIMENSIONS,
    api_key=settings.api_key,
)

class RAGService:

    @staticmethod
    def embed_text(text: str) -> np.ndarray:
        vector = embeddings.embed_query(text)
        return np.array(vector, dtype=np.float32)
