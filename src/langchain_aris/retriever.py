from langchain_community.vectorstores.neo4j_vector import Neo4jVector, SearchType
from langchain_core.vectorstores import VectorStoreRetriever
from langchain_openai import OpenAIEmbeddings

from src.config import NEO4J_HOST, NEO4J_PASSWORD, NEO4J_PORT
from src.logger import logger


def init_retriever(vector_db_id: int, embeddings: OpenAIEmbeddings, **search_kwargs) -> VectorStoreRetriever:
    try:
        node_label = f"knowledge_base:{vector_db_id}"
        vector_db = Neo4jVector(
            username="neo4j",
            url=f"bolt://{NEO4J_HOST}:{NEO4J_PORT}",
            password=NEO4J_PASSWORD,
            node_label=node_label,
            search_type=SearchType.HYBRID,
            embedding=embeddings,
        )
        retriever = vector_db.as_retriever(search_kwargs=search_kwargs)

    except Exception as e:
        raise ValueError(f"Failed to init retriever: {e}")

    logger.debug(f"Init retriever with search kwargs: {search_kwargs}")
    return retriever
