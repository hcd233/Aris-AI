from sqlalchemy import Boolean, Column, Integer, String

from .base import BaseSchema


class UserSchema(BaseSchema):
    """\
    The user schema. Contain some necessary fields.
    """

    __tablename__ = "users"
    uid = Column(Integer, primary_key=True, autoincrement=True)
    user: str = Column(String(255), nullable=False)
    password: str = Column(String(255), nullable=False)
    is_admin: bool = Column(Boolean, nullable=False, default=False)
    api_key: str = Column(String(255), nullable=False)
