import secrets
import string
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String

from .base import BaseSchema
from .user import UserSchema


def generate_api_key_secret() -> str:
    """\
    Generate a random string with length 32.
    """
    return "sk-alice" + "".join(secrets.choice(string.ascii_letters + string.digits) for _ in range(32))


class ApiKeySchema(BaseSchema):
    """\
    The access key schema. Contain some necessary fields.
    """

    __tablename__ = "api_keys"
    ak_id: int = Column(Integer, primary_key=True, autoincrement=True)
    create_at: datetime = Column(DateTime, default=datetime.now)
    update_at: datetime = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    delete_at: datetime = Column(DateTime, nullable=True)
    api_key_secret: str = Column(String(255), nullable=False, default=generate_api_key_secret)
    uid: int = Column(Integer, ForeignKey(UserSchema.uid, ondelete="CASCADE"), nullable=False)
