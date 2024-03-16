from datetime import datetime
from typing import Literal

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String

from .base import BaseSchema
from .users import UserSchema


class EmbeddingSchema(BaseSchema):

    __tablename__ = "embeddings"
    embedding_id: int = Column(Integer, primary_key=True, autoincrement=True)
    embedding_name: str = Column(String(255), nullable=False)
    embedding_type: Literal["openai"] = Column(String(255), nullable=False)
    create_at: datetime = Column(DateTime, default=datetime.now)
    update_at: datetime = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    delete_at: datetime = Column(DateTime, nullable=True)
    base_url: str = Column(String(255), nullable=False)
    api_key: str = Column(String(255), nullable=False, default="")
    chunk_size: int = Column(Integer, nullable=False)
    embed_dim: int = Column(Integer, nullable=False)
    uploader_id: int = Column(Integer, ForeignKey(UserSchema.uid), nullable=False)
