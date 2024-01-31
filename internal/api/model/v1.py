from pydantic import BaseModel


class UserRequest(BaseModel):
    user: str
    password: str


class UidRequest(BaseModel):
    uid: int
