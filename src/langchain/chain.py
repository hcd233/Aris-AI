from langchain_core.messages import SystemMessage
from langchain_core.output_parsers.string import StrOutputParser
from langchain_core.runnables import RunnableParallel, RunnablePassthrough
from langchain_core.runnables.base import Runnable
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.vectorstores import VectorStoreRetriever
from langchain_openai import ChatOpenAI

from src.langchain.embedding import init_embedding
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from src.langchain.retriever import init_retriever
from src.langchain.callback import OUTPUT_PARSER_NAME
from src.langchain.llm import init_llm
from src.langchain.memory import init_history
from src.middleware.mysql.models import EmbeddingSchema, LLMSchema


def init_chat_chain(llm_schema: LLMSchema, temperature: float, session_id: int) -> Runnable:
    llm: ChatOpenAI = init_llm(
        llm_type=llm_schema.llm_type,
        llm_name=llm_schema.llm_name,
        base_url=llm_schema.base_url,
        api_key=llm_schema.api_key,
        temperature=temperature,
        max_tokens=llm_schema.max_tokens,
    )

    chat_prompt: ChatPromptTemplate = SystemMessage(content=llm_schema.sys_prompt) + MessagesPlaceholder(variable_name="history") + "{user_prompt}"
    output_parser = StrOutputParser(name=OUTPUT_PARSER_NAME)

    chain = RunnableWithMessageHistory(
        chat_prompt | llm | output_parser,
        init_history,
        input_messages_key="user_prompt",
        history_messages_key="history",
    ).with_config({"configurable": {"session_id": session_id}})
    return chain


def init_retriever_qa_chain(
    llm_schema: LLMSchema,
    embedding_schema: EmbeddingSchema,
    temperature: float,
    session_id: int,
    vector_db_id,
) -> Runnable:
    llm = init_llm(
        llm_type=llm_schema.llm_type,
        llm_name=llm_schema.llm_name,
        base_url=llm_schema.base_url,
        api_key=llm_schema.api_key,
        temperature=temperature,
        max_tokens=llm_schema.max_tokens,
    )

    embeddings = init_embedding(
        embedding_type=embedding_schema.embedding_type,
        embedding_name=embedding_schema.embedding_name,
        api_key=embedding_schema.api_key,
        base_url=embedding_schema.base_url,
        chunk_size=embedding_schema.chunk_size,
    )

    retriever: VectorStoreRetriever = init_retriever(
        vector_db_id=vector_db_id,
        embeddings=embeddings,
    )

    rag_prompt = SystemMessage(content=llm_schema.sys_prompt) + MessagesPlaceholder(variable_name="history") + "{user_prompt}"
    output_parser = StrOutputParser(name=OUTPUT_PARSER_NAME)

    chain = RunnableWithMessageHistory(
        rag_prompt | llm | output_parser,
        init_history,
        input_messages_key="user_prompt",
        history_messages_key="history",
    ).with_config({"configurable": {"session_id": session_id}})
    chain = RunnableParallel({"context": retriever, "question": RunnablePassthrough()}).assign(answer=chain)

    return chain
