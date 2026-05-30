from contextvars import ContextVar

auth_token: ContextVar[str] = ContextVar("auth_token", default="")
current_user_uuid: ContextVar[str] = ContextVar("current_user_uuid", default="")

# 记录上一次不完整的工具调用（参数收集到一半），用于多轮续接
# 注意：不能用 ContextVar，因为每个 HTTP 请求是独立的 asyncio task，跨请求不共享
_pending_store: dict[str, dict] = {}


def get_pending(user_uuid: str) -> dict | None:
    return _pending_store.pop(user_uuid, None)


def set_pending(user_uuid: str, pending: dict):
    _pending_store[user_uuid] = pending
