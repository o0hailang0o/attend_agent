from sqlalchemy import Column, Integer, String, DateTime
from app.core.database import Base


class SysUser(Base):
    __tablename__ = "sys_user"

    id = Column(Integer, primary_key=True, autoincrement=True)
    sys_user_uuid = Column(String(36), unique=True, nullable=False, comment="UUID")
    account = Column(String(50), unique=True, nullable=False, comment="工号")
    work_num = Column(String(50), nullable=True, comment="工号(备用)")
    name = Column(String(50), nullable=False, comment="姓名")
    dept = Column(String(100), nullable=True, comment="部门")
    position = Column(String(100), nullable=True, comment="职位")
    phone = Column(String(20), nullable=True, comment="手机号")
    email = Column(String(100), nullable=True, comment="邮箱")
    status = Column(Integer, default=1, comment="状态 1=正常 0=禁用")
    created_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, nullable=True)
