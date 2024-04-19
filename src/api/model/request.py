from typing import Literal

from pydantic import BaseModel


class UserRequest(BaseModel):
    user_name: str
    password: str


class UidRequest(BaseModel):
    uid: int


class CreateLLMRequest(BaseModel):
    llm_name: str
    llm_type: Literal["openai"]
    request_type: Literal["string", "message"]
    api_key: str
    base_url: str
    sys_name: str = "system"
    user_name: str = "user"
    ai_name: str = "assistant"
    sys_prompt: str = (
        "A chat between a curious user and an artificial intelligence assistant. \n"
        "The assistant gives helpful, detailed, and polite answers to the user's questions."
    )
    max_tokens: int = 2048


class CreateEmbeddingRequest(BaseModel):
    embedding_name: str
    embedding_type: Literal["openai"]
    base_url: str
    api_key: str
    chunk_size: int
    embed_dim: int


class CreateVectorDbRequest(BaseModel):
    vector_db_name: str
    embedding_name: str
    vector_db_description: str = ""


class ChatRequest(BaseModel):
    llm_name: str
    temperature: float
    message: str
    vector_db_id: int | None = None
