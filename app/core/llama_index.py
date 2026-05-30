from llama_index.core import Settings as LlamaSettings
from llama_index.llms.zhipuai import ZhipuAI
from llama_index.llms.openai import OpenAI
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


def _register_deepseek_models():
    """将 DeepSeek 模型名注册到 llama_index OpenAI 工具类的已知模型列表中，
    避免 openai_modelname_to_contextsize 抛出 Unknown model 错误。"""
    from llama_index.llms.openai import utils as openai_utils

    deepseek_models = {
        "deepseek-chat": 128000,
        "deepseek-v4-flash": 128000,
        "deepseek-v4-pro": 128000,
        "deepseek-reasoner": 128000,
    }
    for name, ctx in deepseek_models.items():
        openai_utils.ALL_AVAILABLE_MODELS[name] = ctx
        openai_utils.CHAT_MODELS[name] = ctx


def get_text_to_sql_llm():
    """返回专用于 text-to-sql SQL 生成的 LLM 实例，支持 zhipu / deepseek 等 provider"""
    key = settings.text_to_sql_llm_api_key or settings.llm_api_key
    model = settings.text_to_sql_llm_model or "glm-4-flash"
    provider = settings.text_to_sql_llm_provider or "zhipu"

    if provider == "deepseek":
        _register_deepseek_models()
        return OpenAI(
            api_key=key,
            model=model,
            api_base=settings.text_to_sql_llm_api_base or "https://api.deepseek.com",
        )
    return ZhipuAI(api_key=key, model=model)


__all__ = ["get_llm", "get_text_to_sql_llm"]
