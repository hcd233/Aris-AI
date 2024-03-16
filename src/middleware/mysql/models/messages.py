from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, Text

from .base import BaseSchema
from .sessions import SessionSchema


class MessageSchema(BaseSchema):

    __tablename__ = "messages"
    id: int = Column(Integer, primary_key=True, autoincrement=True)
    chat_at: datetime = Column(DateTime, default=datetime.now)
    message: str = Column(Text, nullable=False)
    session_id: int = Column(Integer, ForeignKey(SessionSchema.session_id, ondelete="CASCADE"), nullable=False)
