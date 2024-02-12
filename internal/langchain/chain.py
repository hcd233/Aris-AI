from typing import List

from langchain.callbacks.base import BaseCallbackHandler
from langchain.chains import ConversationalRetrievalChain, LLMChain, RetrievalQA, StuffDocumentsChain
from langchain.prompts import ChatPromptTemplate, PromptTemplate
from langchain_core.memory import BaseMemory
from langchain_core.vectorstores import VectorStoreRetriever
from langchain_openai import ChatOpenAI


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
) -> RetrievalQA:
    llm_chain = LLMChain(
        llm=llm,
        prompt=prompt,
    )
    document_prompt = PromptTemplate(input_variables=["page_content"], template="Context:\n{page_content}")
    combine_documents_chain = StuffDocumentsChain(
        llm_chain=llm_chain,
        document_variable_name="context",
        document_prompt=document_prompt,
    )
    chain = RetrievalQA(
        retriever=retriever,
        combine_documents_chain=combine_documents_chain,
        callbacks=callbacks,
        name="retriever_qa_chain",
        input_key="user_prompt",
        verbose=True,
        return_source_documents=True,
        **kwargs,
    )
    return chain


def init_retriever_chat_chain() -> ConversationalRetrievalChain:
    pass
