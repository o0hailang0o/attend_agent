"""请假类型（leave_type）码值 ↔ 中文名称 双向转换，数据从数据库加载"""

import logging
from typing import Optional, Union

from app.core.database import SessionLocal

logger = logging.getLogger(__name__)

_CACHE: dict[int, str] | None = None
_REVERSE_CACHE: dict[str, int] | None = None

_ALIASES = {"公休假": 7, "补休": 7}


def _load_from_db() -> tuple[dict[int, str], dict[str, int]]:
    """从 leave_type 表加载 id→name 映射"""
    from sqlalchemy import text

    session = SessionLocal()
    try:
        rows = session.execute(
            text("SELECT id, name FROM leave_type WHERE is_delete = 1")
        ).fetchall()
        forward = {row[0]: row[1] for row in rows}
        reverse = {row[1]: row[0] for row in rows}
        logger.info("从数据库加载 leave_type: %s", forward)
        return forward, reverse
    except Exception as e:
        logger.warning("加载 leave_type 失败: %s", e)
        raise
    finally:
        session.close()


def _get_maps():
    global _CACHE, _REVERSE_CACHE
    if _CACHE is None:
        _CACHE, _REVERSE_CACHE = _load_from_db()
    return _CACHE, _REVERSE_CACHE


def refresh_cache():
    """强制刷新缓存（数据库 leave_type 变更后调用）"""
    global _CACHE, _REVERSE_CACHE
    _CACHE = None
    _REVERSE_CACHE = None
    _get_maps()


class LeaveTypeConverter:
    """请假类型码值 ↔ 中文名称，数据实时从数据库 leave_type 表加载

    int → str: LeaveTypeConverter.to_name(1)   → "年假"
    str → int: LeaveTypeConverter.to_code("年假") → 1
    str → int: LeaveTypeConverter.to_code("公休假") → 7 (别名)
    """

    @staticmethod
    def to_name(code: int) -> str:
        forward, _ = _get_maps()
        return forward.get(code, str(code))

    @staticmethod
    def to_code(name: str) -> Optional[int]:
        if name in _ALIASES:
            return _ALIASES[name]
        _, reverse = _get_maps()
        return reverse.get(name)

    @staticmethod
    def convert(value: Union[int, str]) -> Optional[Union[str, int]]:
        if isinstance(value, int):
            return LeaveTypeConverter.to_name(value)
        return LeaveTypeConverter.to_code(value)
