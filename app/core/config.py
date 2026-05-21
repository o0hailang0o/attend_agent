from pathlib import Path
from typing import Optional

import yaml
from pydantic_settings import BaseSettings


class MySQLSettings(BaseSettings):
    host: str = "127.0.0.1"
    port: int = 3306
    user: str = "root"
    password: str = ""
    database: str = "attend_agent"
    pool_size: int = 10


class RedisSettings(BaseSettings):
    host: str = "127.0.0.1"
    port: int = 6379
    db: int = 0
    password: Optional[str] = None


class LLMSettings(BaseSettings):
    provider: str = "openai"
    model: str = "gpt-4o-mini"
    api_key: str = ""
    api_base: Optional[str] = None
    temperature: float = 0.0
    max_tokens: int = 4096


class AppSettings(BaseSettings):
    name: str = "attend-agent"
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = True


class Settings(BaseSettings):
    app: AppSettings
    mysql: MySQLSettings
    redis: RedisSettings
    llm: LLMSettings

    @classmethod
    def load(cls, path: str = "settings.yml") -> "Settings":
        p = Path(path)
        if not p.exists():
            raise FileNotFoundError(f"Settings file not found: {path}")
        with open(p, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return cls(**data)


settings = Settings.load()
