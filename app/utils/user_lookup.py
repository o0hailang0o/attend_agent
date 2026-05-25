from typing import Tuple, Optional
from app.models import SysUser
from app.core.database import get_db


def resolve_user(identifier: str) -> Optional[str]:
    """根据标识符（工号或姓名）解析用户 UUID"""
    db = next(get_db())

    if identifier.isdigit():
        user = db.query(SysUser).filter(
            (SysUser.account == identifier) | (SysUser.work_num == identifier)
        ).first()
    else:
        user = db.query(SysUser).filter(SysUser.name == identifier).first()
        if not user:
            user = db.query(SysUser).filter(SysUser.name.like(f"%{identifier}%")).first()

    if user:
        return user.sys_user_uuid
    return None


def get_sys_user_uuid(name: str, work_num: str) -> Optional[str]:
    """根据姓名和工号查询 sysUserUuid

    Args:
        name: 员工姓名
        work_num: 员工工号

    Returns:
        sysUserUuid 字符串，未匹配时返回 None
    """
    db = next(get_db())
    try:
        user = db.query(SysUser).filter(
            SysUser.name == name,
            SysUser.work_num == work_num
        ).first()
        if user:
            return user.sys_user_uuid
        return None
    finally:
        db.close()