import datetime
from typing import Tuple

from fastapi import APIRouter, Depends
from sqlalchemy import func, or_

from internal.langchain.llm import init_llm, ping_llm
from internal.middleware.mysql import session
from internal.middleware.mysql.model import LLMSchema

from ...auth import sk_auth
from ...model.request import CreateLLMRequest
from ...model.response import StandardResponse

model_router = APIRouter(prefix="/model", tags=["model"])


@model_router.get("/llms", response_model=StandardResponse, dependencies=[Depends(sk_auth)])
async def get_model_list():
    with session() as conn:
        if not conn.is_active:
            conn.rollback()
            conn.close()
        else:
            conn.commit()

        query = conn.query(LLMSchema.llm_id, LLMSchema.llm_name).filter(
            or_(LLMSchema.delete_at.is_(None), datetime.datetime.now() < LLMSchema.delete_at)
        )
        result = query.all()

    data = {"llm_list": [{"llm_id": llm_id, "llm_name": llm_name} for (llm_id, llm_name) in result]}

    return StandardResponse(code=0, status="success", message="Get llm list successfully", data=data)


@model_router.post("/llm/newLLM", response_model=StandardResponse, dependencies=[Depends(sk_auth)])
async def create_llm(request: CreateLLMRequest, info: Tuple[int, int] = Depends(sk_auth)):
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
            conn.query(LLMSchema)
            .filter(LLMSchema.llm_name == request.llm_name)
            .filter(LLMSchema.api_key == request.api_key)
            .filter(LLMSchema.base_url == request.base_url)
        )
        result = query.first()

        if result:
            return StandardResponse(code=1, status="error", message="Model name already exist")

        llm = init_llm(llm_type=request.llm_type, llm_name=request.llm_name, base_url=request.base_url, api_key=request.api_key)
        if not llm:
            return StandardResponse(code=1, status="error", message="Invalid LLM type")
        pong = ping_llm(llm=llm)

        if not pong:
            return StandardResponse(code=1, status="error", message="Ping LLM failed. Check your config.")

        llm = LLMSchema(
            llm_name=request.llm_name,
            llm_type=request.llm_type,
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

    return StandardResponse(code=0, status="success", message="Create model successfully", data=data)


@model_router.get("/llm/{model_id}", response_model=StandardResponse, dependencies=[Depends(sk_auth)])
async def get_model_info(model_id: int):
    with session() as conn:
        if not conn.is_active:
            conn.rollback()
            conn.close()
        else:
            conn.commit()

        query = (
            conn.query(
                LLMSchema.llm_id,
                LLMSchema.llm_name,
                func.date(LLMSchema.create_at),
                func.date(LLMSchema.update_at),
                LLMSchema.max_tokens,
            )
            .filter(LLMSchema.llm_id == model_id)
            .filter(or_(LLMSchema.delete_at.is_(None), datetime.datetime.now() < LLMSchema.delete_at))
        )
        result = query.first()

    if not result:
        return StandardResponse(code=1, status="error", message="Model not exist")

    llm_id, name, create_at, update_at, max_tokens = result
    data = {
        "llm_id": llm_id,
        "llm_name": name,
        "create_at": create_at,
        "update_at": update_at,
        "max_tokens": max_tokens,
    }

    return StandardResponse(code=0, status="success", message="Get model info successfully", data=data)
