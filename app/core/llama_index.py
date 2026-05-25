from llama_index.core import Settings as LlamaSettings
from llama_index.llms.zhipuai import ZhipuAI
from app.core.settings import settings


def get_llm():
    if not settings.llm_api_key:
        raise ValueError("LLM API key not configured")

    llm = ZhipuAI(
        api_key=settings.llm_api_key,
        model=settings.llm_model,
    )
    LlamaSettings.llm = llm
    return llm


__all__ = ["get_llm"]
