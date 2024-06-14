from datetime import datetime
from typing import Literal

from src.middleware.jwt import encode_token
from src.middleware.mysql import session
from src.middleware.mysql.models import UserSchema


def login(name: str, unique_id: str, avatar: str, platform: Literal["github"]) -> str:
    with session() as conn:
        if not conn.is_active:
            conn.rollback()
            conn.close()
        else:
            conn.commit()

        query = conn.query(UserSchema.uid, UserSchema.is_admin).filter(UserSchema.unique_id == unique_id).filter(UserSchema.platform == platform)
        result = query.first()

    if result:
        (uid, is_admin) = result
    else:
        uid, is_admin = register(name, unique_id, avatar, platform), 0

    with session() as conn:
        if not conn.is_active:
            conn.rollback()
            conn.close()
        else:
            conn.commit()

        conn.query(UserSchema).filter(UserSchema.uid == uid).update({UserSchema.last_login: datetime.now()})
        conn.flush()
        conn.commit()

    return encode_token(uid=uid, level=is_admin)


def register(name: str, unique_id: str, avatar: str, platform: Literal["github"]) -> int:
    with session() as conn:
        if not conn.is_active:
            conn.rollback()
            conn.close()
        else:
            conn.commit()

        user = UserSchema(
            name=name,
            unique_id=unique_id,
            avatar=avatar,
            platform=platform,
        )
        conn.add(user)
        conn.flush()
        conn.commit()

        uid = user.uid

    return uid
