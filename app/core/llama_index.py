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


def get_text_to_sql_llm():
    """返回专用于 text-to-sql SQL 生成的 LLM 实例（可配不同的模型，如更轻量的 glm-4-flash）"""
    key = settings.text_to_sql_llm_api_key or settings.llm_api_key
    model = settings.text_to_sql_llm_model or "glm-4-flash"
    base = settings.text_to_sql_llm_api_base or settings.llm_api_base
    return ZhipuAI(api_key=key, model=model)


__all__ = ["get_llm", "get_text_to_sql_llm"]
