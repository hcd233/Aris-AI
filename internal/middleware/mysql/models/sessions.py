from datetime import datetime
from typing import Any, Dict, List

from sqlalchemy import JSON, Column, DateTime, ForeignKey, Integer

from .base import BaseSchema
from .users import UserSchema


class SessionSchema(BaseSchema):
    """\
    The user schema. Contain some necessary fields.
    """

    __tablename__ = "sessions"
    session_id: int = Column(Integer, primary_key=True, autoincrement=True)
    create_at: datetime = Column(DateTime, default=datetime.now)
    update_at: datetime = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    delete_at: datetime = Column(DateTime, nullable=True)
    conversation: List[Dict[str, Any]] = Column(JSON, nullable=False, default=[])
    uid: int = Column(Integer, ForeignKey(UserSchema.uid, ondelete="CASCADE"), nullable=False)
