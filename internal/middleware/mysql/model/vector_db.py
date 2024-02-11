from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String

from .base import BaseSchema
from .embeddings import EmbeddingSchema
from .users import UserSchema


class VectorDbSchema(BaseSchema):

    __tablename__ = "vector_dbs"
    vector_db_id: int = Column(Integer, primary_key=True, autoincrement=True)
    vector_db_name: str = Column(String(255), nullable=False)
    vector_db_description: str = Column(String(255), nullable=True)
    db_size: int = Column(Integer, nullable=False, default=0)
    create_at: datetime = Column(DateTime, default=datetime.now)
    update_at: datetime = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    delete_at: datetime = Column(DateTime, nullable=True)
    embedding_id: int = Column(Integer, ForeignKey(EmbeddingSchema.embedding_id), nullable=False)
    uid: int = Column(Integer, ForeignKey(UserSchema.uid), nullable=False)
