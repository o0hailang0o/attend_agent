from typing import Optional

from llama_index.core import Settings as LlamaSettings
from llama_index.llms.openai import OpenAI

from app.core.config import settings

_llm: Optional[OpenAI] = None


def get_llm() -> OpenAI:
    global _llm
    if _llm is None:
        kwargs = dict(
            model=settings.llm.model,
            temperature=settings.llm.temperature,
            max_tokens=settings.llm.max_tokens,
            api_key=settings.llm.api_key,
        )
        if settings.llm.api_base:
            kwargs["api_base"] = settings.llm.api_base
        _llm = OpenAI(**kwargs)
        LlamaSettings.llm = _llm
    return _llm
