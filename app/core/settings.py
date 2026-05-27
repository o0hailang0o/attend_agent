from pathlib import Path
from typing import Optional
import yaml
from pydantic import Field
from pydantic_settings import BaseSettings


def _load_yaml_settings() -> dict:
    yml_path = Path(__file__).resolve().parent.parent.parent / "settings.yml"
    if not yml_path.exists():
        return {}
    with open(yml_path, encoding="utf-8") as f:
        raw = yaml.safe_load(f) or {}
    flat = {}
    db = raw.get("database", {})
    flat["database_host"] = "192.168.31.100"
    flat["database_port"] = 3306
    flat["database_user"] = db.get("username", "root")
    flat["database_password"] = db.get("password", "root123")
    flat["database_db"] = "attend"
    if db.get("url"):
        from urllib.parse import urlparse
        parsed = urlparse(db["url"].replace("jdbc:mysql://", "mysql://"))
        flat["database_host"] = parsed.hostname or "192.168.31.100"
        flat["database_port"] = parsed.port or 3306
        flat["database_db"] = parsed.path.lstrip("/") if parsed.path else "attend"

    redis = raw.get("redis", {})
    flat["redis_host"] = redis.get("host", "192.168.31.100")
    flat["redis_port"] = redis.get("port", 6379)
    flat["redis_password"] = redis.get("password", "123456")

    llm = raw.get("llm", {})
    flat["llm_api_key"] = llm.get("api-key", "")
    flat["llm_model"] = llm.get("model", "GLM-4.5-Air")
    flat["llm_api_base"] = llm.get("api-base", "https://open.bigmodel.cn/api/paas/v4/")

    attend = raw.get("attend", {})
    flat["attend_base_url"] = attend.get("base-url", "http://192.168.31.100:8080")

    t2s = raw.get("text-to-sql-llm", {})
    flat["text_to_sql_llm_api_key"] = t2s.get("api-key", "")
    flat["text_to_sql_llm_model"] = t2s.get("model", "glm-4-flash")
    flat["text_to_sql_llm_api_base"] = t2s.get("api-base", "https://open.bigmodel.cn/api/paas/v4/")
    return flat


class Settings(BaseSettings):
    database_host: str = "192.168.31.100"
    database_port: int = 3306
    database_user: str = "root"
    database_password: str = "root123"
    database_db: str = "attend"

    redis_host: str = "192.168.31.100"
    redis_port: int = 6379
    redis_password: str = "123456"

    llm_api_key: str = ""
    llm_model: str = "glm-4-air"
    llm_api_base: str = "https://open.bigmodel.cn/api/paas/v4/"

    attend_base_url: str = "http://localhost:8080"

    text_to_sql_llm_api_key: str = ""
    text_to_sql_llm_model: str = "glm-4-flash"
    text_to_sql_llm_api_base: str = "https://open.bigmodel.cn/api/paas/v4/"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

    @property
    def database_url(self) -> str:
        return f"mysql+aiomysql://{self.database_user}:{self.database_password}@{self.database_host}:{self.database_port}/{self.database_db}"

    @property
    def database_url_sync(self) -> str:
        return f"mysql+pymysql://{self.database_user}:{self.database_password}@{self.database_host}:{self.database_port}/{self.database_db}"


_yaml_overrides = _load_yaml_settings()
settings = Settings(**_yaml_overrides)
