from token import OP
from typing import Dict

from langchain_openai.embeddings import OpenAIEmbeddings

from src.logger import logger

EMBEDDING_TYPE_CLS_MAP: Dict[str, OpenAIEmbeddings] = {
    "openai": OpenAIEmbeddings,
}


def init_embedding(embedding_type: str, embedding_name: str, api_key: str, base_url: str, chunk_size: int, **kwargs) -> OpenAIEmbeddings:
    """Init Embedding."""
    embedding_cls = EMBEDDING_TYPE_CLS_MAP.get(embedding_type)
    if not embedding_cls:
        raise ValueError(f"Invalid Embedding type: {embedding_type}")

    embedding: OpenAIEmbeddings = embedding_cls(
        model=embedding_name,
        api_key=api_key,
        base_url=base_url,
        chunk_size=chunk_size,
        **kwargs,
    )
    logger.debug(f"Init Embedding: {embedding.model}")
    return embedding


def ping_embedding(embedding: OpenAIEmbeddings, embed_dim: int) -> bool:
    """Ping Embedding to check if it is available."""

    try:
        embedding_vector = embedding.embed_query("Ping!")
        if len(embedding_vector) != embed_dim:
            logger.error(f"Embedding vector length mismatch: {len(embedding_vector)}")
            return False
        logger.debug(f"Ping Embedding vector(first three dims):{[round(d, 3) for d in embedding_vector[:3]]}")
    except Exception as e:
        logger.error(f"Ping Embedding failed: {e}")
        return False

    logger.info(f"Ping Embedding successfully: {embedding.model}")
    return True
