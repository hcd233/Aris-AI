import secrets
import string

from fastapi import APIRouter
from pydantic import BaseModel

from internal.middleware.mysql import session
from internal.middleware.mysql.models import UserSchema

from ...base import StandardResponse

user_router = APIRouter(prefix="/user")


class UserRequest(BaseModel):
    user: str
    password: str


@user_router.post("/register")
def register_user(request: UserRequest):
    with session() as conn:
        query = conn.query(UserSchema.user).filter(UserSchema.user == request.user)
        exist_user = query.first()

    if exist_user:
        return StandardResponse(code=1, status="error", message="User already exist")

    api_key = "sk-" + "".join(secrets.choice(string.ascii_letters + string.digits) for _ in range(32))
    with session() as conn:
        if not conn.is_active:
            conn.rollback()

        user = UserSchema(user=request.user, password=request.password, api_key=api_key)
        conn.add(user)
        conn.commit()

    return StandardResponse(code=0, status="success", message="Register successfully")
