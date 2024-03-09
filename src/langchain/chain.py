from typing import List

from langchain_core.memory import BaseMemory
from langchain_core.output_parsers.string import StrOutputParser
from langchain_core.runnables import RunnableConfig, RunnableParallel, RunnablePassthrough, RunnableSerializable
from langchain_core.vectorstores import VectorStoreRetriever
from langchain_openai import ChatOpenAI

from langchain.callbacks.base import BaseCallbackHandler
from langchain.chains import ConversationalRetrievalChain, LLMChain
from langchain.prompts import ChatPromptTemplate


def init_chat_chain(llm: ChatOpenAI, prompt: ChatPromptTemplate, memory: BaseMemory, callbacks: List[BaseCallbackHandler], **kwargs) -> LLMChain:
    chain = LLMChain(
        name="multi_turn_chat_llm_chain",
        llm=llm,
        prompt=prompt,
        memory=memory,
        verbose=True,
        return_final_only=True,
        callbacks=callbacks,
        **kwargs,
    )

    return chain


def init_retriever_qa_chain(
    llm: ChatOpenAI, prompt: ChatPromptTemplate, retriever: VectorStoreRetriever, callbacks: List[BaseCallbackHandler], **kwargs
) -> RunnableSerializable:
    output_parser = StrOutputParser()  # convert AI message to string

    config = RunnableConfig(callbacks=callbacks)
    chain = (prompt | llm | output_parser).with_config(config)
    chain = RunnableParallel({"context": retriever, "question": RunnablePassthrough()}).assign(answer=chain)
    return chain


def init_retriever_chat_chain() -> ConversationalRetrievalChain:
    pass
