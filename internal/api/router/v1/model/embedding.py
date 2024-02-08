from datetime import datetime
from json import dumps, loads
from typing import Tuple

from fastapi import APIRouter, Depends
from sqlalchemy import func, or_

from internal.langchain.embedding import init_embedding, ping_embedding
from internal.middleware.mysql import session
from internal.middleware.mysql.model import EmbeddingSchema
from internal.middleware.redis import r

from ....auth import jwt_auth, sk_auth
from ....model.request import CreateEmbeddingRequest
from ....model.response import StandardResponse

embedding_router = APIRouter(prefix="/embedding", tags=["embedding"])


@embedding_router.post("", response_model=StandardResponse, dependencies=[Depends(jwt_auth)])
def create_embedding(request: CreateEmbeddingRequest, info: Tuple[int, int] = Depends(jwt_auth)) -> StandardResponse:
    uid, level = info

    if not level:
        return StandardResponse(code=1, status="error", message="No permission to create Embedding model")

    redis_hashmap = "embeddings"
    if r.exists(redis_hashmap):
        if r.hexists(redis_hashmap, request.embedding_name):
            return StandardResponse(code=1, status="error", message=f"Embedding name: `{request.embedding_name}` already exist")

    else:
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
            r.hset(redis_hashmap, request.embedding_name, result.embedding_id)
            return StandardResponse(code=1, status="error", message=f"Embedding name: `{request.embedding_name}` already exist")

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

    with session() as conn:
        if not conn.is_active:
            conn.rollback()
            conn.close()
        else:
            conn.commit()

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
        conn.commit()

        data = {"embedding_id": embedding.embedding_id}
        r.hset(redis_hashmap, request.embedding_name, embedding.embedding_id)
        redis_key = f"embed_id:{embedding.embedding_id}"
        r.delete(redis_key)

    return StandardResponse(code=0, status="success", message="Create Embedding successfully", data=data)


@embedding_router.get("/embeddings", response_model=StandardResponse, dependencies=[Depends(sk_auth)])
async def get_embedding_list():
    redis_hashmap = "embeddings"
    if r.exists(redis_hashmap):
        result = r.hgetall(redis_hashmap)
        embedding_list = [{"embedding_id": v, "embedding_name": k} for k, v in result.items()]

    else:
        with session() as conn:
            if not conn.is_active:
                conn.rollback()
                conn.close()
            else:
                conn.commit()

            query = conn.query(EmbeddingSchema.embedding_id, EmbeddingSchema.embedding_name).filter(
                or_(EmbeddingSchema.delete_at.is_(None), datetime.now() < EmbeddingSchema.delete_at)
            )
            result = query.all()

        embedding_list = [
            {
                "embedding_id": embedding_id,
                "embedding_name": embedding_name,
            }
            for (embedding_id, embedding_name) in result
        ]
        for embedding in embedding_list:
            r.hset(redis_hashmap, embedding["embedding_name"], embedding["embedding_id"])

    data = {"embedding_list": embedding_list}

    return StandardResponse(code=0, status="success", message="Get Embedding list successfully", data=data)


@embedding_router.get("/{embedding_id}", response_model=StandardResponse, dependencies=[Depends(sk_auth)])
async def get_embedding_info(embedding_id: int):

    redis_key = f"embed_id:{embedding_id}"
    info = r.get(redis_key)
    match info:
        case "not_exist":
            return StandardResponse(code=1, status="error", message=f"Embedding id: {embedding_id} not exist")

        case None:
            with session() as conn:
                if not conn.is_active:
                    conn.rollback()
                    conn.close()
                else:
                    conn.commit()

                query = (
                    conn.query(
                        EmbeddingSchema.embedding_name,
                        func.date(EmbeddingSchema.create_at),
                        func.date(EmbeddingSchema.update_at),
                        EmbeddingSchema.chunk_size,
                        EmbeddingSchema.embed_dim,
                    )
                    .filter(EmbeddingSchema.embedding_id == embedding_id)
                    .filter(or_(EmbeddingSchema.delete_at.is_(None), datetime.now() < EmbeddingSchema.delete_at))
                )
                result = query.first()

            if not result:
                return StandardResponse(code=1, status="error", message=f"Embedding id: {embedding_id} not exist")

            embedding_name, create_at, update_at, chunk_size, embed_dim = result
            data = {
                "embedding_id": embedding_id,
                "embedding_name": embedding_name,
                "create_at": str(create_at),
                "update_at": str(update_at),
                "chunk_size": chunk_size,
                "embed_dim": embed_dim,
            }
            r.set(redis_key, dumps(data, ensure_ascii=False))

        case _:
            data = loads(info)

    return StandardResponse(code=0, status="success", message="Get Embedding info successfully", data=data)
