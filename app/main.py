import json
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from app.api.routes.chat import router
from app.api.routes.agent_api import router as agent_router
from app.core.database import engine, Base
from app.core import redis as redis_module
from app.context import auth_token, current_user_uuid
from app.models import Session, Message  # noqa: ensure models registered for table creation

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    await redis_module.init_redis()
    try:
        yield
    finally:
        await redis_module.close_redis()


app = FastAPI(lifespan=lifespan)

app.include_router(router, prefix="/api/v1")
app.include_router(agent_router, prefix="/api/v1")


@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    if request.url.path in ("/health", "/docs", "/openapi.json", "/redoc"):
        return await call_next(request)

    token = request.headers.get("Authorization", "").removeprefix("Bearer ").strip()
    if not token:
        return JSONResponse(status_code=401, content={"detail": "未提供认证令牌"})
    try:
        r = redis_module.redis
        raw = await r.get(f"sysUser_{token}") if r else None
        if not raw:
            return JSONResponse(status_code=401, content={"detail": "登录已过期，请重新登录"})
        user_uuid = json.loads(raw).get("uuid", "")
        if not user_uuid:
            return JSONResponse(status_code=401, content={"detail": "用户信息无效"})
    except Exception as e:
        logger.warning("Auth middleware failed: %s", e)
        return JSONResponse(status_code=401, content={"detail": "登录状态异常，请重新登录"})

    tok = auth_token.set(token)
    uid_tok = current_user_uuid.set(user_uuid)
    try:
        return await call_next(request)
    finally:
        auth_token.reset(tok)
        current_user_uuid.reset(uid_tok)


@app.get("/health")
def health_check():
    return {"status": "healthy"}