from contextvars import ContextVar

auth_token: ContextVar[str] = ContextVar("auth_token", default="")
current_user_uuid: ContextVar[str] = ContextVar("current_user_uuid", default="")

# 记录上一次不完整的工具调用（参数收集到一半），用于多轮续接
pending_tool_call: ContextVar[dict | None] = ContextVar("pending_tool_call", default=None)
