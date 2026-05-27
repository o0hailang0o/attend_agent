import uuid
from sqlalchemy import Column, String, DateTime, func
from app.core.database import Base


class Session(Base):
    __tablename__ = "sessions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_uuid = Column(String(64), nullable=False, index=True, comment="用户 UUID")
    title = Column(String(200), default="新对话", comment="会话标题")
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")
