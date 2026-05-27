from sqlalchemy import Column, Integer, BigInteger, String, DateTime
from app.core.database import Base


class SysUser(Base):
    __tablename__ = "sys_user"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    uuid = Column(String(64), nullable=False, comment="UUID")
    name = Column(String(32), nullable=False, comment="姓名")
    account = Column(String(32), nullable=False, comment="工号")
    password = Column(String(1000), nullable=False, comment="密码")
    nick_name = Column(String(32), nullable=True, comment="昵称")
    gender = Column(Integer, nullable=False, comment="性别")
    work_num = Column(String(32), nullable=True, comment="工号(备用)")
    dept_uuid = Column(String(64), nullable=True, comment="部门UUID")
    dept_name = Column(String(32), nullable=True, comment="部门名称")
    position_uuid = Column(String(64), nullable=True, comment="职位UUID")
    position = Column(String(32), nullable=True, comment="职位")
    level = Column(String(16), nullable=True, comment="级别")
    rule_uuid = Column(String(64), nullable=True, comment="考勤规则UUID")
    rule_name = Column(String(32), nullable=True, comment="考勤规则名称")
    company_id = Column(String(64), nullable=True, comment="公司ID")
    is_delete = Column(Integer, default=1, comment="1正常 0删除")
    create_time = Column(DateTime, nullable=True)
    update_time = Column(DateTime, nullable=True)
