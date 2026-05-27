import logging
from app.core.database import SessionLocal
from app.models.message import Message

logger = logging.getLogger(__name__)

MAX_HISTORY = 20


async def load_history(user_uuid: str) -> list[dict]:
    """从 MySQL 加载最近对话历史"""
    try:
        db = SessionLocal()
        try:
            rows = (
                db.query(Message)
                .filter(Message.user_uuid == user_uuid)
                .order_by(Message.id.desc())
                .limit(MAX_HISTORY)
                .all()
            )
            history = []
            for row in reversed(rows):
                history.append({"role": row.role, "content": row.content})
            return history
        finally:
            db.close()
    except Exception as e:
        logger.warning("Failed to load chat history: %s", e)
        return []


async def save_message(user_uuid: str, role: str, content: str):
    """保存消息到 MySQL"""
    try:
        db = SessionLocal()
        try:
            msg = Message(user_uuid=user_uuid, role=role, content=content)
            db.add(msg)
            db.commit()
        finally:
            db.close()
    except Exception as e:
        logger.warning("Failed to save chat message: %s", e)


async def clear_history(user_uuid: str):
    """清除用户对话历史"""
    try:
        db = SessionLocal()
        try:
            db.query(Message).filter(Message.user_uuid == user_uuid).delete()
            db.commit()
        finally:
            db.close()
    except Exception as e:
        logger.warning("Failed to clear chat history: %s", e)
