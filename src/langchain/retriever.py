from pathlib import Path

from langchain_community.vectorstores.faiss import FAISS
from langchain_core.vectorstores import VectorStoreRetriever
from langchain_openai import OpenAIEmbeddings

from src.config import FAISS_ROOT
from src.logger import logger


def init_retriever(vector_db_id: int, embedding: OpenAIEmbeddings, **kwargs) -> VectorStoreRetriever | None:
    try:
        local_path = Path(FAISS_ROOT) / str(vector_db_id) / "vector_db"
        vector_db = FAISS.load_local(local_path, embedding)
        retriever = vector_db.as_retriever(search_kwargs=kwargs)

    except Exception as e:
        logger.error(f"Failed to init retriever: {e}")
        return None

    logger.debug(f"Init retriever with args: {kwargs}")
    return retriever
