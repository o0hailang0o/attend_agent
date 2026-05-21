from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import settings


class Base(DeclarativeBase):
    pass


engine = create_engine(
    f"mysql+aiomysql://{settings.mysql.user}:{settings.mysql.password}"
    f"@{settings.mysql.host}:{settings.mysql.port}/{settings.mysql.database}",
    pool_size=settings.mysql.pool_size,
    echo=settings.app.debug,
    future=True,
)

async_session_factory = sessionmaker(engine, expire_on_commit=False)


def get_engine():
    return engine


def get_session_factory():
    return async_session_factory
