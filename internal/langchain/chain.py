from langchain.chains import ConversationalRetrievalChain, LLMChain, RetrievalQA
from langchain.prompts import ChatPromptTemplate
from langchain_core.memory import BaseMemory
from langchain_core.vectorstores import VectorStoreRetriever
from langchain_openai import ChatOpenAI


def init_chat_chain(llm: ChatOpenAI, prompt: ChatPromptTemplate, memory: BaseMemory) -> LLMChain:
    chain = LLMChain(
        name="multi_turn_chat_llm_chain",
        llm=llm,
        prompt=prompt,
        memory=memory,
        verbose=True,
        return_final_only=True,
    )

    return chain


def init_retriever_qa_chain(llm: ChatOpenAI, prompt: ChatPromptTemplate, retriever: VectorStoreRetriever) -> RetrievalQA:
    chain = RetrievalQA.from_llm(
        llm=llm,
        prompt=prompt,
        retriever=retriever,
        name="retriever_qa_chain",
        input_key="user_prompt",
        verbose=True,
        return_source_documents=True,
    )
    return chain


def init_retriever_chat_chain() -> ConversationalRetrievalChain:
    pass
