from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Integer, String

from .base import BaseSchema


class UserSchema(BaseSchema):

    __tablename__ = "users"
    uid: int = Column(Integer, primary_key=True, autoincrement=True)
    create_at: datetime = Column(DateTime, default=datetime.now)
    update_at: datetime = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    delete_at: datetime = Column(DateTime, nullable=True)
    user: str = Column(String(255), nullable=False)
    password: str = Column(String(255), nullable=False)
    is_admin: bool = Column(Boolean, nullable=False, default=False)
    ak_num: int = Column(Integer, nullable=False, default=0)
