from contextvars import ContextVar

auth_token: ContextVar[str] = ContextVar("auth_token", default="")
current_user_uuid: ContextVar[str] = ContextVar("current_user_uuid", default="")
