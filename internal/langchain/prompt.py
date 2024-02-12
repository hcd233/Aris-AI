from typing import Literal

from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder, PromptTemplate
from langchain_core.messages import SystemMessage
from langchain_core.prompts import HumanMessagePromptTemplate, SystemMessagePromptTemplate

# NOTE It just inserts system prompt into user prompt
chat_template = """\
{sys_name}:{sys_prompt}
{history}
{user_name}:{user_prompt}
{ai_name}:\
"""


def init_chat_prompt(
    sys_prompt: str, request_type: Literal["message", "string"], sys_name: str, user_name: str, ai_name: str
) -> ChatPromptTemplate | PromptTemplate:
    match request_type:
        case "message":
            chat_prompt: ChatPromptTemplate = SystemMessage(content=sys_prompt) + MessagesPlaceholder(variable_name="history") + "{user_prompt}"
        case "string":
            input_variables = ["user_prompt", "history"]
            template = chat_template.format(
                sys_name=sys_name,
                sys_prompt=sys_prompt,
                user_name=user_name,
                ai_name=ai_name,
                **{var: f"{{{var}}}" for var in input_variables},  # not replace
            )

            chat_prompt = PromptTemplate(
                input_variables=input_variables,
                template=template,
            )
        case _:
            raise ValueError(f"Invalid request_type: {request_type}")
    return chat_prompt


retriever_prompt_prefix = "\nUse the following pieces of context to answer the question at the end. If you don't know the answer, just say that you don't know, don't try to make up an answer.\n{context}"

retriever_template = """\
{sys_name}:{sys_prompt}
{user_name}:{user_prompt}
{ai_name}:\
"""


def init_retriever_prompt(
    sys_prompt: str, request_type: Literal["message", "string"], sys_name: str, user_name: str, ai_name: str
) -> ChatPromptTemplate | PromptTemplate:
    sys_prompt += retriever_prompt_prefix

    match request_type:
        case "message":
            retriever_prompt = ChatPromptTemplate.from_messages(
                [SystemMessagePromptTemplate.from_template(sys_prompt), HumanMessagePromptTemplate.from_template("{question}")]
            )
        case "string":
            input_variables = ["user_prompt", "context"]
            template = chat_template.format(
                sys_name=sys_name,
                sys_prompt=sys_prompt,
                user_name=user_name,
                ai_name=ai_name,
                **{var: f"{{{var}}}" for var in input_variables},  # not replace
            )

            retriever_prompt = PromptTemplate(
                input_variables=input_variables,
                template=template,
            )
        case _:
            raise ValueError(f"Invalid request_type: {request_type}")
    return retriever_prompt
