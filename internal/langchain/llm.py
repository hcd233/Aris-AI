from typing import Dict

from langchain_openai.chat_models import ChatOpenAI

from internal.logger import logger

LLM_TYPE_CLS_MAP: Dict[str, ChatOpenAI] = {
    "openai": ChatOpenAI,
}


def init_llm(llm_type: str, llm_name: str, base_url: str, api_key: str, **kwargs) -> ChatOpenAI | None:
    """Init LLM."""
    llm_cls = LLM_TYPE_CLS_MAP.get(llm_type)
    if not llm_cls:
        logger.error(f"Invalid LLM type: {llm_type}")
        return None

    kwargs.update(
        {
            "verbose": True,
            "streaming": True,
        }
    )

    llm = llm_cls(name=llm_name, model_name=llm_name, base_url=base_url, api_key=api_key, **kwargs)
    logger.debug(f"Init LLM: {llm.model_name}")
    return llm


def ping_llm(llm: ChatOpenAI) -> bool:
    """Ping LLM to check if it is available."""

    try:
        llm_reply = llm.invoke("Ping! Please reply with 'Pong!'")
        logger.debug(f"Ping LLM reply: {llm_reply.content}")
    except Exception as e:
        logger.error(f"Ping LLM failed: {e}")
        return False

    logger.info(f"Ping LLM successfully: {llm.model_name}")
    return True
