import json
from typing import Any

from langchain.memory import ConversationBufferWindowMemory
from langchain.memory.chat_memory import BaseChatMemory
from langchain_community.chat_message_histories import SQLChatMessageHistory
from langchain_community.chat_message_histories.sql import BaseMessageConverter
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.messages import BaseMessage, message_to_dict, messages_from_dict

from internal.middleware.mysql import MYSQL_LINK
from internal.middleware.mysql.model import MessageSchema


class SessionsMessageConverter(BaseMessageConverter):
    """The class responsible for converting BaseMessage to your SQLAlchemy model."""

    def __init__(self):
        self.model_class = MessageSchema

    def from_sql_model(self, sql_message: Any) -> BaseMessage:
        return messages_from_dict([json.loads(sql_message.message)])[0]

    def to_sql_model(self, message: BaseMessage, session_id: int) -> Any:
        return self.model_class(session_id=session_id, message=json.dumps(message_to_dict(message)))

    def get_sql_model_class(self) -> Any:
        return self.model_class


def init_history(session_id: int) -> BaseChatMessageHistory:
    """Init memory."""
    sessions_message_converter = SessionsMessageConverter()
    history = SQLChatMessageHistory(
        session_id=session_id,
        connection_string=MYSQL_LINK,
        custom_message_converter=sessions_message_converter,
    )

    return history


def init_str_memory(history: BaseChatMessageHistory, user_name: str, ai_name: str, **kwargs) -> BaseChatMemory:
    memory = ConversationBufferWindowMemory(
        chat_memory=history,
        human_prefix=user_name,
        ai_prefix=ai_name,
        return_messages=False,
        **kwargs,
    )
    return memory


def init_msg_memory(history: BaseChatMessageHistory, **kwargs) -> BaseChatMemory:
    memory = ConversationBufferWindowMemory(
        chat_memory=history,
        return_messages=True,
        **kwargs,
    )
    return memory
