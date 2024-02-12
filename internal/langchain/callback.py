import sys
from queue import Queue
from typing import Any, Dict, List
from uuid import UUID

from langchain_core.callbacks.base import BaseCallbackHandler
from langchain_core.outputs import ChatGenerationChunk, GenerationChunk, LLMResult

from internal.api.model.response import SSEResponse
from internal.middleware.redis import r


class TokenGenerator:
    def __init__(self, redis_lock: str):
        self.redis_lock = redis_lock
        self.queue = Queue()

        r.set(self.redis_lock, "lock", ex=30)

    def __iter__(self):
        return self

    def __next__(self):
        item = self.queue.get()
        if item is StopIteration:
            raise item
        return item

    def send(self, data: str):
        self.queue.put(data + "\n")

    def close(self):
        self.queue.put(StopIteration)
        r.delete(self.redis_lock)


class StreamCallbackHandler(BaseCallbackHandler):
    def __init__(self, token_generator: TokenGenerator) -> None:
        self.token_generator = token_generator
        self.chain_num: int = 0

    def on_chain_start(
        self,
        serialized: Dict[str, Any],
        inputs: Dict[str, Any],
        *,
        run_id: UUID,
        parent_run_id: UUID | None = None,
        tags: List[str] | None = None,
        metadata: Dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> Any:
        data = SSEResponse(status="chain:start", delta="", extras={})
        self.token_generator.send(data.model_dump_json())
        self.chain_num += 1

    def on_chain_end(self, outputs: Dict[str, Any], *, run_id: UUID, parent_run_id: UUID | None = None, **kwargs: Any) -> Any:
        if "source_documents" in outputs:
            outputs["source_documents"] = [doc.page_content for doc in outputs["source_documents"]]
        data = SSEResponse(status="chain:end", delta="", extras={"outputs": outputs})
        self.token_generator.send(data.model_dump_json())
        self.chain_num -= 1
        if not self.chain_num:
            self.token_generator.close()

    def on_llm_start(
        self,
        serialized: Dict[str, Any],
        prompts: List[str],
        *,
        run_id: UUID,
        parent_run_id: UUID | None = None,
        tags: List[str] | None = None,
        metadata: Dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> Any:
        data = SSEResponse(status="llm:start", delta="", extras={})
        self.token_generator.send(data.model_dump_json())

    def on_llm_new_token(
        self,
        token: str,
        *,
        chunk: GenerationChunk | ChatGenerationChunk | None = None,
        run_id: UUID,
        parent_run_id: UUID | None = None,
        **kwargs: Any,
    ) -> Any:
        sys.stdout.write(token)
        sys.stdout.flush()
        data = SSEResponse(status="llm:new_token", delta=token, extras={})
        self.token_generator.send(data.model_dump_json())

    def on_llm_end(self, response: LLMResult, *, run_id: UUID, parent_run_id: UUID | None = None, **kwargs: Any) -> Any:
        data = SSEResponse(status="llm:end", delta="", extras={})
        self.token_generator.send(data.model_dump_json())
