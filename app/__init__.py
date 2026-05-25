from .core.config import settings
from .core.database import engine, Base

try:
    from .core.redis import init_redis, close_redis
except Exception:
    init_redis = None
    close_redis = None

try:
    from .api.routes import chat_router
except Exception:
    chat_router = None

__all__ = ["settings", "engine", "Base", "init_redis", "close_redis", "chat_router"]
