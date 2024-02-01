from typing import Dict

from langchain_openai.chat_models import ChatOpenAI

from internal.logger import logger

LLM_TYPE_CLS_MAP: Dict[str, ChatOpenAI] = {
    "openai": ChatOpenAI,
}


def ping_llm(llm_type: str, llm_name: str, base_url: str, api_key: str) -> bool:
    """Ping LLM to check if it is available."""
    llm_cls = LLM_TYPE_CLS_MAP.get(llm_type)
    if not llm_cls:
        logger.error(f"Invalid LLM type: {llm_type}")
        return False

    llm = llm_cls(model=llm_name, base_url=base_url, api_key=api_key)
    try:
        llm_reply = llm.invoke("Ping! Please reply with 'Pong!'")
        logger.debug(f"Ping LLM reply: {llm_reply.content}")
    except Exception as e:
        logger.error(f"Ping LLM failed: {e}")
        return False

    logger.info(f"Ping LLM successfully: {llm_name}")
    return True
