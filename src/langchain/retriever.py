from pathlib import Path

from langchain_community.vectorstores.faiss import FAISS
from langchain_core.vectorstores import VectorStoreRetriever
from langchain_openai import OpenAIEmbeddings

from src.config import FAISS_ROOT
from src.logger import logger


def init_retriever(vector_db_id: int, embeddings: OpenAIEmbeddings, **kwargs) -> VectorStoreRetriever:
    try:
        local_path = Path(FAISS_ROOT) / str(vector_db_id) / "vector_db"
        vector_db = FAISS.load_local(local_path, embeddings=embeddings)
        retriever = vector_db.as_retriever(search_kwargs=kwargs)

    except Exception as e:
        raise ValueError(f"Failed to init retriever: {e}")

    logger.debug(f"Init retriever with args: {kwargs}")
    return retriever
