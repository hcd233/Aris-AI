from datetime import datetime
from typing import Literal

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String

from .base import BaseSchema
from .users import UserSchema


class LLMSchema(BaseSchema):

    __tablename__ = "llms"
    llm_id: int = Column(Integer, primary_key=True, autoincrement=True)
    llm_name: str = Column(String(255), nullable=False)
    llm_type: Literal["openai"] = Column(String(255), nullable=False)
    request_type: Literal["string", "message"] = Column(String(255), nullable=False)
    create_at: datetime = Column(DateTime, default=datetime.now)
    update_at: datetime = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    delete_at: datetime = Column(DateTime, nullable=True)
    base_url: str = Column(String(255), nullable=False)
    api_key: str = Column(String(255), nullable=False, default="")
    sys_name: str = Column(String(255), nullable=False, default="system")
    sys_prompt: str = Column(String(255), nullable=False, default="")
    user_name: str = Column(String(255), nullable=False, default="user")
    ai_name: str = Column(String(255), nullable=False, default="AI")
    max_tokens: int = Column(Integer, nullable=False, default=2048)
    uploader_id: int = Column(Integer, ForeignKey(UserSchema.uid), nullable=False)
