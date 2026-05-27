import logging
from typing import Optional
import httpx
from app.models import SysUser
from app.core.database import get_db
from app.core.settings import settings
from app.context import current_user_uuid

logger = logging.getLogger(__name__)

_SELF_KEYWORDS = {"我", "本人", "当前用户", "当前", "自己"}


def _resolve_user_from_attend_api(identifier: str) -> Optional[str]:
    """本地 DB 查不到时，降级调用 attend 接口搜索用户"""
    try:
        base_url = settings.attend_base_url or "http://192.168.31.100:8080"
        resp = httpx.get(f"{base_url}/sysuser", params={"name": identifier}, timeout=10)
        if resp.status_code != 200:
            return None
        body = resp.json()
        data = body.get("data") if isinstance(body, dict) else None
        if not data:
            return None
        users = data if isinstance(data, list) else data.get("records", [data])
        if users and isinstance(users, list):
            for u in users:
                uuid = u.get("uuid") or u.get("id")
                if uuid:
                    return str(uuid)
        return None
    except Exception as e:
        logger.warning("降级调用 attend API 搜索用户失败: %s", e)
        return None


def resolve_user(identifier: str) -> Optional[str]:
    """根据标识符（工号、账号或姓名）解析用户 UUID。空字符串视为当前用户。

    降级策略：
    1. 先查本地 sys_user 表（精确匹配 account / work_num / name）
    2. 本地查不到时调用 attend API GET /sysuser?name={identifier} 搜索
    3. 都查不到返回 None
    """
    if not identifier or identifier in _SELF_KEYWORDS:
        uuid = current_user_uuid.get()
        if uuid:
            return uuid
        logger.warning("当前用户 UUID 未设置，无法解析「%s」", identifier)
        return None

    try:
        db = next(get_db())
    except Exception as e:
        logger.error("获取数据库连接失败: %s", e)
        return _resolve_user_from_attend_api(identifier)
    try:
        if any(c.isdigit() for c in identifier):
            user = db.query(SysUser).filter(
                SysUser.is_delete == 1,
                (SysUser.account == identifier) | (SysUser.work_num == identifier)
            ).first()
        else:
            user = db.query(SysUser).filter(
                SysUser.is_delete == 1,
                SysUser.name == identifier
            ).first()
            if not user:
                user = db.query(SysUser).filter(
                    SysUser.is_delete == 1,
                    SysUser.name.like(f"%{identifier}%")
                ).first()

        if user:
            return user.uuid
        return _resolve_user_from_attend_api(identifier)
    except Exception as e:
        logger.error("查询用户异常: %s", e)
        return _resolve_user_from_attend_api(identifier)
    finally:
        try:
            db.close()
        except Exception:
            pass


def get_sys_user_uuid(name: str, work_num: str) -> Optional[str]:
    """根据姓名和工号查询 sysUserUuid

    Args:
        name: 员工姓名
        work_num: 员工工号

    Returns:
        sysUserUuid 字符串，未匹配时返回 None
    """
    try:
        db = next(get_db())
    except Exception as e:
        logger.error("获取数据库连接失败: %s", e)
        return None
    try:
        user = db.query(SysUser).filter(
            SysUser.is_delete == 1,
            SysUser.name == name,
            SysUser.work_num == work_num
        ).first()
        if user:
            return user.uuid
        return None
    except Exception as e:
        logger.error("查询用户异常: %s", e)
        return None
    finally:
        try:
            db.close()
        except Exception:
            pass