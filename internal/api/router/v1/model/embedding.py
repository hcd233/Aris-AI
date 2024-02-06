from typing import Tuple

from fastapi import APIRouter, Depends

from internal.langchain.embedding import init_embedding, ping_embedding
from internal.middleware.mysql import session
from internal.middleware.mysql.model import EmbeddingSchema

from ....auth import jwt_auth
from ....model.request import CreateEmbeddingRequest
from ....model.response import StandardResponse

embedding_router = APIRouter(prefix="/embedding", tags=["embedding"])


@embedding_router.post("", response_model=StandardResponse, dependencies=[Depends(jwt_auth)])
def create_embedding(request: CreateEmbeddingRequest, info: Tuple[int, int] = Depends(jwt_auth)) -> StandardResponse:
    uid, level = info

    if not level:
        return StandardResponse(code=1, status="error", message="No permission")

    with session() as conn:
        if not conn.is_active:
            conn.rollback()
            conn.close()
        else:
            conn.commit()

        query = (
            conn.query(EmbeddingSchema)
            .filter(EmbeddingSchema.embedding_name == request.embedding_name)
            .filter(EmbeddingSchema.api_key == request.api_key)
            .filter(EmbeddingSchema.base_url == request.base_url)
        )
        result = query.first()

        if result:
            return StandardResponse(code=1, status="error", message="Model name already exist")

        embedding = init_embedding(
            embedding_type=request.embedding_type,
            embedding_name=request.embedding_name,
            base_url=request.base_url,
            api_key=request.api_key,
            chunk_size=request.chunk_size,
        )

        if not embedding:
            return StandardResponse(code=1, status="error", message=f"Invalid Embedding type: {request.embedding_type}")
        pong = ping_embedding(embedding=embedding, embed_dim=request.embed_dim)

        if not pong:
            return StandardResponse(code=1, status="error", message="Ping Embedding failed. Check your config.")

        embedding = EmbeddingSchema(
            embedding_name=request.embedding_name,
            embedding_type=request.embedding_type,
            base_url=request.base_url,
            api_key=request.api_key,
            chunk_size=request.chunk_size,
            embed_dim=request.embed_dim,
            uploader_id=uid,
        )

        conn.add(embedding)

        return StandardResponse(code=0, status="success", message="Embedding model created")
