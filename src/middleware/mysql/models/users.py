from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Integer, String

from .base import BaseSchema


class UserSchema(BaseSchema):

    __tablename__ = "users"
    uid: int = Column(Integer, primary_key=True, autoincrement=True)
    unique_id: str = Column(String(100), nullable=False, unique=True)
    name: str = Column(String(100), nullable=False)
    avatar: str = Column(String(255), nullable=False)
    platform: str = Column(String(50), nullable=False)
    create_at: datetime = Column(DateTime, default=datetime.now)
    update_at: datetime = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    delete_at: datetime = Column(DateTime, nullable=True)
    last_login: datetime = Column(DateTime, nullable=True, default=datetime.now)
    is_admin: bool = Column(Boolean, nullable=False, default=False)
    ak_num: int = Column(Integer, nullable=False, default=0)
