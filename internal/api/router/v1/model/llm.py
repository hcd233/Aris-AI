from datetime import datetime
from json import dumps, loads
from typing import Tuple

from fastapi import APIRouter, Depends
from sqlalchemy import func, or_

from internal.langchain.llm import init_llm, ping_llm
from internal.middleware.mysql import session
from internal.middleware.mysql.model import LLMSchema
from internal.middleware.redis import r

from ....auth import jwt_auth, sk_auth
from ....model.request import CreateLLMRequest
from ....model.response import StandardResponse

llm_router = APIRouter(prefix="/llm", tags=["llm"])
embedding_router = APIRouter(prefix="/embedding", tags=["embedding"])


@llm_router.post("", response_model=StandardResponse, dependencies=[Depends(jwt_auth)])
async def create_llm(request: CreateLLMRequest, info: Tuple[int, int] = Depends(jwt_auth)):
    uid, level = info

    if not level:
        return StandardResponse(code=1, status="error", message="No permission to create LLM")

    redis_hashmap = "llms"
    if r.exists(redis_hashmap):
        if r.hexists(redis_hashmap, request.llm_name):
            return StandardResponse(code=1, status="error", message=f"LLM name: `{request.llm_name}` already exist")

    else:
        with session() as conn:
            if not conn.is_active:
                conn.rollback()
                conn.close()
            else:
                conn.commit()

            query = (
                conn.query(LLMSchema)
                .filter(LLMSchema.llm_name == request.llm_name)
                .filter(LLMSchema.api_key == request.api_key)
                .filter(LLMSchema.base_url == request.base_url)
            )
            result = query.first()

            if result:
                r.hset(redis_hashmap, request.llm_name, result.llm_id)
                return StandardResponse(code=1, status="error", message=f"LLM name: `{request.llm_name}` already exist")

    llm = init_llm(
        llm_type=request.llm_type,
        llm_name=request.llm_name,
        base_url=request.base_url,
        api_key=request.api_key,
    )
    if not llm:
        return StandardResponse(code=1, status="error", message=f"Invalid LLM type {request.llm_type}")
    pong = ping_llm(llm=llm)

    if not pong:
        return StandardResponse(code=1, status="error", message="Ping LLM failed. Check your config.")

    with session() as conn:
        if not conn.is_active:
            conn.rollback()
            conn.close()
        else:
            conn.commit()

        llm = LLMSchema(
            llm_name=request.llm_name,
            llm_type=request.llm_type,
            request_type=request.request_type,
            base_url=request.base_url,
            api_key=request.api_key,
            sys_name=request.sys_name,
            sys_prompt=request.sys_prompt.rstrip() + "\n",
            user_name=request.user_name,
            ai_name=request.ai_name,
            max_tokens=request.max_tokens,
            uploader_id=uid,
        )

        conn.add(llm)
        conn.commit()

        data = {"llm_id": llm.llm_id}
        r.hset(redis_hashmap, request.llm_name, llm.llm_id)
        r.delete(f"llm_id:{llm.llm_id}")

    return StandardResponse(code=0, status="success", data=data)


@llm_router.get("/llms", response_model=StandardResponse, dependencies=[Depends(sk_auth)])
async def get_llm_list():
    redis_hashmap = "llms"

    if r.exists(redis_hashmap):
        result = r.hgetall(redis_hashmap)
        data = {"llm_list": [{"llm_id": v, "llm_name": k} for k, v in result.items()]}
        return StandardResponse(code=0, status="success", data=data)

    with session() as conn:
        if not conn.is_active:
            conn.rollback()
            conn.close()
        else:
            conn.commit()

        query = conn.query(LLMSchema.llm_id, LLMSchema.llm_name).filter(or_(LLMSchema.delete_at.is_(None), datetime.now() < LLMSchema.delete_at))
        result = query.all()

    llm_list = [{"llm_id": llm_id, "llm_name": llm_name} for (llm_id, llm_name) in result]
    for llm in llm_list:
        r.hset(redis_hashmap, llm["llm_name"], llm["llm_id"])
    data = {"llm_list": llm_list}

    return StandardResponse(code=0, status="success", data=data)


@llm_router.get("/{llm_id}", response_model=StandardResponse, dependencies=[Depends(sk_auth)])
async def get_llm_info(llm_id: int):
    redis_key = f"llm_id:{llm_id}"
    info = r.get(redis_key)

    if info == "not_exist":
        return StandardResponse(code=1, status="error", message=f"LLM id: {llm_id} not exist")

    if info is not None:
        data = loads(info)
        return StandardResponse(code=0, status="success", data=data)

    with session() as conn:
        if not conn.is_active:
            conn.rollback()
            conn.close()
        else:
            conn.commit()

        query = (
            conn.query(
                LLMSchema.llm_name,
                func.date(LLMSchema.create_at),
                func.date(LLMSchema.update_at),
                LLMSchema.max_tokens,
            )
            .filter(LLMSchema.llm_id == llm_id)
            .filter(or_(LLMSchema.delete_at.is_(None), datetime.now() < LLMSchema.delete_at))
        )
        result = query.first()

    if not result:
        r.set(redis_key, "not_exist", ex=300)
        return StandardResponse(code=1, status="error", message=f"LLM id: {llm_id} not exist")

    name, create_at, update_at, max_tokens = result
    data = {
        "llm_id": llm_id,
        "llm_name": name,
        "create_at": str(create_at),
        "update_at": str(update_at),
        "max_tokens": max_tokens,
    }

    r.set(redis_key, dumps(data, ensure_ascii=False), ex=300)

    return StandardResponse(code=0, status="success", data=data)
