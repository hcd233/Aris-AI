from fastapi import APIRouter
from pydantic import BaseModel

from internal.middleware.mysql import session
from internal.middleware.mysql.models import ApiKeySchema, UserSchema

from ...base import StandardResponse

user_router = APIRouter(prefix="/user", tags=["user"])


class UserRequest(BaseModel):
    user: str
    password: str


@user_router.post("/register")
def register_user(request: UserRequest) -> StandardResponse:
    with session() as conn:
        query = conn.query(UserSchema.user).filter(UserSchema.user == request.user)
        exist_user = query.first()

    if exist_user:
        return StandardResponse(code=1, status="error", message="User already exist")

    with session() as conn:
        if not conn.is_active:
            conn.rollback()

        user = UserSchema(user=request.user, password=request.password)
        conn.add(user)
        conn.commit()

    return StandardResponse(code=0, status="success", message="Register successfully")


@user_router.post("/key/generate")
def generate_api_key(request: UserRequest) -> StandardResponse:
    with session() as conn:
        query = conn.query(UserSchema.uid, UserSchema.ak_num).filter(UserSchema.user == request.user and UserSchema.password == request.password)
        result = query.first()

    if not result:
        return StandardResponse(code=1, status="error", message="User not exist or password incorrect")

    (uid, ak_num) = result

    if ak_num >= 5:
        return StandardResponse(code=1, status="error", message="You can only generate 5 keys at most")

    with session() as conn:
        if not conn.is_active:
            conn.rollback()

        api_key = ApiKeySchema(uid=uid)
        conn.add(api_key)
        conn.query(UserSchema).filter(UserSchema.uid == uid).update({"ak_num": UserSchema.ak_num + 1})
        conn.commit()
        data = {"api_key_secret": api_key.api_key_secret}

    return StandardResponse(
        code=0,
        status="success",
        message="Generate key successfully. Please save it carefully.",
        data=data,
    )
