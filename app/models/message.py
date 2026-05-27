from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, func
from app.core.database import Base


class Message(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(36), nullable=True, index=True, comment="会话 ID")
    user_uuid = Column(String(64), nullable=True, index=True, comment="用户 UUID")
    role = Column(String(16), nullable=False, comment="user / assistant")
    content = Column(Text, nullable=False, comment="消息内容")
    title = Column(String(200), nullable=True, comment="消息标题")
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
