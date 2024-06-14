from datetime import datetime
from pathlib import Path
from typing import List, Tuple

from fastapi import APIRouter, BackgroundTasks, Depends, UploadFile
from langchain_community.vectorstores.neo4j_vector import Neo4jVector, SearchType
from langchain_openai.embeddings import OpenAIEmbeddings
from sqlalchemy import or_

from src.config import NEO4J_HOST, NEO4J_PASSWORD, NEO4J_PORT, SUPPORT_UPLOAD_FILE, TMP_ROOT
from src.langchain_aris.embedding import init_embedding
from src.langchain_aris.file_loader import load_upload_files
from src.langchain_aris.text_splitter import split_documents
from src.langchain_aris.url_loader import load_upload_urls
from src.logger import logger
from src.middleware.mysql import session
from src.middleware.mysql.models import EmbeddingSchema, VectorDbSchema

from ...auth import sk_auth
from ...model.request import CreateVectorDbRequest, UploadUrlsRequest
from ...model.response import StandardResponse

vector_db_router = APIRouter(prefix="/vector-db", tags=["vector-db"])


def _embedding_task(vector_db_id: int, documents: List[str], embedding: OpenAIEmbeddings) -> None:
    logger.debug(f"Start async task: embedding {len(documents)} docs for vector_db_id: {vector_db_id}")
    try:
        node_label = f"knowledge_base:{vector_db_id}"
        vector_db = Neo4jVector(
            username="neo4j",
            url=f"bolt://{NEO4J_HOST}:{NEO4J_PORT}",
            password=NEO4J_PASSWORD,
            node_label=node_label,
            search_type=SearchType.HYBRID,
            embedding=embedding,
        )
        vector_db.add_documents(documents)
    except Exception as e:
        logger.error(f"Error when embedding {len(documents)} docs for vector_db_id: {vector_db_id}, error: {e}")
    else:
        logger.debug(f"Finish async task: embedding {len(documents)} docs for vector_db_id: {vector_db_id}")


@vector_db_router.post("", response_model=StandardResponse, dependencies=[Depends(sk_auth)])
def create_vector_db(request: CreateVectorDbRequest, info: Tuple[str, str] = Depends(sk_auth)):
    uid, _ = info
    with session() as conn:
        if not conn.is_active:
            conn.rollback()
            conn.close()
        else:
            conn.commit()

        query = (
            conn.query(VectorDbSchema.vector_db_id)
            .filter(VectorDbSchema.vector_db_name == request.vector_db_name)
            .filter(VectorDbSchema.uid == uid)
            .filter(or_(VectorDbSchema.delete_at.is_(None), datetime.now() < VectorDbSchema.delete_at))
        )
        result = query.first()

    if result:
        return StandardResponse(code=1, status="error", message=f"Vector DB `{request.vector_db_name}` already exists")

    with session() as conn:
        query = (
            conn.query(EmbeddingSchema.embedding_id)
            .filter(EmbeddingSchema.embedding_name == request.embedding_name)
            .filter(or_(EmbeddingSchema.delete_at.is_(None), datetime.now() < EmbeddingSchema.delete_at))
        )
        result = query.first()

    if not result:
        return StandardResponse(code=1, status="error", message=f"Embedding `{request.embedding_name}` does not exist")

    (embedding_id,) = result

    with session() as conn:
        vector_db = VectorDbSchema(
            uid=uid,
            vector_db_name=request.vector_db_name,
            embedding_id=embedding_id,
            vector_db_description=request.vector_db_description,
        )
        conn.add(vector_db)
        conn.commit()

        data = {"vector_db_id": vector_db.vector_db_id}

    return StandardResponse(code=0, status="success", data=data)


@vector_db_router.get("/vector-dbs", response_model=StandardResponse, dependencies=[Depends(sk_auth)])
def get_vector_dbs(info: Tuple[str, str] = Depends(sk_auth)):
    uid, _ = info
    with session() as conn:
        if not conn.is_active:
            conn.rollback()
            conn.close()
        else:
            conn.commit()

        query = (
            conn.query(
                VectorDbSchema.vector_db_id,
                VectorDbSchema.vector_db_name,
                VectorDbSchema.create_at,
                VectorDbSchema.update_at,
            )
            .filter(VectorDbSchema.uid == uid)
            .filter(or_(VectorDbSchema.delete_at.is_(None), datetime.now() < VectorDbSchema.delete_at))
        )
        result = query.all()
    vector_db_list = [
        {
            "vector_db_id": vector_db_id,
            "vector_db_name": vector_db_name,
            "create_at": str(create_at),
            "update_at": str(update_at),
        }
        for vector_db_id, vector_db_name, create_at, update_at in result
    ]

    data = {"vector_db_list": vector_db_list}

    return StandardResponse(code=0, status="success", data=data)


@vector_db_router.get("/{vector_db_id}", response_model=StandardResponse, dependencies=[Depends(sk_auth)])
def get_vector_db(vector_db_id: int, info: Tuple[str, str] = Depends(sk_auth)):
    uid, _ = info
    with session() as conn:
        if not conn.is_active:
            conn.rollback()
            conn.close()
        else:
            conn.commit()

        query = (
            conn.query(
                VectorDbSchema.vector_db_name,
                VectorDbSchema.create_at,
                VectorDbSchema.update_at,
                VectorDbSchema.vector_db_description,
                VectorDbSchema.db_size,
                EmbeddingSchema.embedding_name,
            )
            .join(EmbeddingSchema, VectorDbSchema.embedding_id == EmbeddingSchema.embedding_id)
            .filter(VectorDbSchema.vector_db_id == vector_db_id)
            .filter(VectorDbSchema.uid == uid)
            .filter(or_(VectorDbSchema.delete_at.is_(None), datetime.now() < VectorDbSchema.delete_at))
        )
        result = query.first()

    if not result:
        return StandardResponse(code=1, status="error", message=f"Vector DB id `{vector_db_id}` does not exist")

    vector_db_name, create_at, update_at, vector_db_description, db_size, embedding_name = result

    data = {
        "vector_db_id": vector_db_id,
        "vector_db_name": vector_db_name,
        "create_at": str(create_at),
        "update_at": str(update_at),
        "vector_db_description": vector_db_description,
        "db_size": db_size,
        "embedding_name": embedding_name,
    }

    return StandardResponse(code=0, status="success", data=data)


@vector_db_router.post("/{vector_db_id}/files", response_model=StandardResponse, dependencies=[Depends(sk_auth)])
def upload_files_to_vector_db(
    vector_db_id: int,
    files: List[UploadFile],
    chunk_size: int,
    chunk_overlap: int,
    background_tasks: BackgroundTasks,
    info: Tuple[str, str] = Depends(sk_auth),
):
    uid, _ = info

    with session() as conn:
        if not conn.is_active:
            conn.rollback()
            conn.close()
        else:
            conn.commit()

        query = (
            conn.query(VectorDbSchema.embedding_id)
            .filter(VectorDbSchema.vector_db_id == vector_db_id)
            .filter(VectorDbSchema.uid == uid)
            .filter(or_(VectorDbSchema.delete_at.is_(None), datetime.now() < VectorDbSchema.delete_at))
        )
        result = query.first()
    if not result:
        return StandardResponse(code=1, status="error", message=f"Vector DB id `{vector_db_id}` does not exist")

    (embedding_id,) = result

    with session() as conn:
        if not conn.is_active:
            conn.rollback()
            conn.close()
        else:
            conn.commit()

        query = (
            conn.query(
                EmbeddingSchema.embedding_type,
                EmbeddingSchema.embedding_name,
                EmbeddingSchema.base_url,
                EmbeddingSchema.api_key,
                EmbeddingSchema.chunk_size,
            )
            .filter(EmbeddingSchema.embedding_id == embedding_id)
            .filter(or_(EmbeddingSchema.delete_at.is_(None), datetime.now() < EmbeddingSchema.delete_at))
        )
        result = query.first()

    if not result:
        return StandardResponse(code=1, status="error", message=f"Bind embedding id `{embedding_id}` does not exist")

    embedding_type, embedding_name, base_url, api_key, _chunk_size = result
    embedding = init_embedding(embedding_type, embedding_name, api_key, base_url, _chunk_size)

    chunk_size = min(chunk_size, _chunk_size)

    invalid = []

    paths: List[Path] = []

    tmp_root = Path(TMP_ROOT)
    tmp_root.mkdir(exist_ok=True, parents=True)

    for file in files:
        path = tmp_root / file.filename
        if path.suffix[1:] not in SUPPORT_UPLOAD_FILE:
            invalid.append(file.filename)
            continue

        with path.open("wb") as f:
            f.write(file.file.read())

        paths.append(path)

    if not paths:
        return StandardResponse(code=1, status="error", message="No file is uploaded")

    documents = load_upload_files(paths)
    if not documents:
        return StandardResponse(code=1, status="error", message="No document is loaded")

    for path in paths:
        path.unlink()

    documents = split_documents(documents, chunk_size, chunk_overlap)

    background_tasks.add_task(_embedding_task, vector_db_id, documents, embedding)

    with session() as conn:
        if not conn.is_active:
            conn.rollback()
            conn.close()
        else:
            conn.commit()

        query = (
            conn.query(VectorDbSchema)
            .filter(VectorDbSchema.vector_db_id == vector_db_id)
            .filter(VectorDbSchema.uid == uid)
            .filter(or_(VectorDbSchema.delete_at.is_(None), datetime.now() < VectorDbSchema.delete_at))
        )
        query.update({VectorDbSchema.db_size: VectorDbSchema.db_size + len(documents)})
        conn.commit()

    data = {
        "embedding_name": embedding_name,
        "upload_size": len(documents),
        "invalid_files": invalid,
    }

    return StandardResponse(code=0, status="success", data=data)


@vector_db_router.post("/{vector_db_id}/urls", response_model=StandardResponse, dependencies=[Depends(sk_auth)])
def upload_urls_to_vector_db(
    vector_db_id: int,
    request: UploadUrlsRequest,
    background_tasks: BackgroundTasks,
    info: Tuple[str, str] = Depends(sk_auth),
):
    uid, _ = info

    with session() as conn:
        if not conn.is_active:
            conn.rollback()
            conn.close()
        else:
            conn.commit()

        query = (
            conn.query(VectorDbSchema.embedding_id)
            .filter(VectorDbSchema.vector_db_id == vector_db_id)
            .filter(VectorDbSchema.uid == uid)
            .filter(or_(VectorDbSchema.delete_at.is_(None), datetime.now() < VectorDbSchema.delete_at))
        )
        result = query.first()
    if not result:
        return StandardResponse(code=1, status="error", message=f"Vector DB id `{vector_db_id}` does not exist")

    (embedding_id,) = result

    with session() as conn:
        if not conn.is_active:
            conn.rollback()
            conn.close()
        else:
            conn.commit()

        query = (
            conn.query(
                EmbeddingSchema.embedding_type,
                EmbeddingSchema.embedding_name,
                EmbeddingSchema.base_url,
                EmbeddingSchema.api_key,
                EmbeddingSchema.chunk_size,
            )
            .filter(EmbeddingSchema.embedding_id == embedding_id)
            .filter(or_(EmbeddingSchema.delete_at.is_(None), datetime.now() < EmbeddingSchema.delete_at))
        )
        result = query.first()

    if not result:
        return StandardResponse(code=1, status="error", message=f"Bind embedding id `{embedding_id}` does not exist")

    embedding_type, embedding_name, base_url, api_key, _chunk_size = result
    embedding = init_embedding(embedding_type, embedding_name, api_key, base_url, _chunk_size)

    chunk_size = min(request.chunk_size, _chunk_size)

    urls = set(request.urls)

    documents = load_upload_urls(list(urls), request.url_type)
    if not documents:
        return StandardResponse(code=1, status="error", message="No document is loaded")

    documents = split_documents(documents, chunk_size, request.chunk_overlap)

    background_tasks.add_task(_embedding_task, vector_db_id, documents, embedding)

    with session() as conn:
        if not conn.is_active:
            conn.rollback()
            conn.close()
        else:
            conn.commit()

        query = (
            conn.query(VectorDbSchema)
            .filter(VectorDbSchema.vector_db_id == vector_db_id)
            .filter(VectorDbSchema.uid == uid)
            .filter(or_(VectorDbSchema.delete_at.is_(None), datetime.now() < VectorDbSchema.delete_at))
        )
        query.update({VectorDbSchema.db_size: VectorDbSchema.db_size + len(documents)})
        conn.commit()

    data = {
        "embedding_name": embedding_name,
        "upload_size": len(documents),
    }

    return StandardResponse(code=0, status="success", data=data)


@vector_db_router.delete("/{vector_db_id}", response_model=StandardResponse, dependencies=[Depends(sk_auth)])
def delete_vector_db(vector_db_id: int, info: Tuple[str, str] = Depends(sk_auth)):
    uid, _ = info
    with session() as conn:
        if not conn.is_active:
            conn.rollback()
            conn.close()
        else:
            conn.commit()

        query = (
            conn.query(VectorDbSchema)
            .filter(VectorDbSchema.vector_db_id == vector_db_id)
            .filter(VectorDbSchema.uid == uid)
            .filter(or_(VectorDbSchema.delete_at.is_(None), datetime.now() < VectorDbSchema.delete_at))
        )
        result = query.first()

    if not result:
        return StandardResponse(code=1, status="error", message=f"Vector DB id `{vector_db_id}` does not exist")

    with session() as conn:
        if not conn.is_active:
            conn.rollback()
            conn.close()
        else:
            conn.commit()

        query = (
            conn.query(VectorDbSchema)
            .filter(VectorDbSchema.vector_db_id == vector_db_id)
            .filter(VectorDbSchema.uid == uid)
            .filter(or_(VectorDbSchema.delete_at.is_(None), datetime.now() < VectorDbSchema.delete_at))
        )
        query.update({VectorDbSchema.delete_at: datetime.now()})
        conn.commit()

    return StandardResponse(code=0, status="success", message="Delete vector_db successfully")
