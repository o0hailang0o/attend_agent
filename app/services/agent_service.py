import logging
import uuid
from datetime import datetime
from app.core.database import SessionLocal
from app.models.session import Session
from app.models.message import Message

logger = logging.getLogger(__name__)

MAX_HISTORY = 50


def list_sessions(user_uuid: str) -> list[dict]:
    try:
        db = SessionLocal()
        try:
            rows = (
                db.query(Session)
                .filter(Session.user_uuid == user_uuid)
                .order_by(Session.updated_at.desc())
                .all()
            )
            return [
                {
                    "id": s.id,
                    "title": s.title,
                    "created_at": s.created_at.isoformat() if s.created_at else None,
                    "updated_at": s.updated_at.isoformat() if s.updated_at else None,
                }
                for s in rows
            ]
        finally:
            db.close()
    except Exception as e:
        logger.warning("Failed to list sessions: %s", e)
        return []


def create_session(user_uuid: str, title: str = "新对话") -> dict | None:
    try:
        db = SessionLocal()
        try:
            session = Session(
                id=str(uuid.uuid4()),
                user_uuid=user_uuid,
                title=title,
            )
            db.add(session)
            db.commit()
            session_id = session.id
        finally:
            db.close()

        # 添加初始助手欢迎消息
        save_message(session_id, "assistant", "你好！我是考勤小助手，有什么可以帮你的吗？")

        return {
            "id": session_id,
            "title": title,
            "created_at": session.created_at.isoformat() if session.created_at else None,
            "updated_at": session.updated_at.isoformat() if session.updated_at else None,
        }
    except Exception as e:
        logger.warning("Failed to create session: %s", e)
        return None


def get_session(session_id: str) -> dict | None:
    try:
        db = SessionLocal()
        try:
            s = db.query(Session).filter(Session.id == session_id).first()
            if not s:
                return None
            return {
                "id": s.id,
                "title": s.title,
                "user_uuid": s.user_uuid,
                "created_at": s.created_at.isoformat() if s.created_at else None,
                "updated_at": s.updated_at.isoformat() if s.updated_at else None,
            }
        finally:
            db.close()
    except Exception as e:
        logger.warning("Failed to get session: %s", e)
        return None


def rename_session(session_id: str, title: str) -> bool:
    try:
        db = SessionLocal()
        try:
            row = db.query(Session).filter(Session.id == session_id).first()
            if not row:
                return False
            row.title = title
            row.updated_at = datetime.now()
            db.commit()
            return True
        finally:
            db.close()
    except Exception as e:
        logger.warning("Failed to rename session: %s", e)
        return False


def delete_session(session_id: str) -> bool:
    try:
        db = SessionLocal()
        try:
            row = db.query(Session).filter(Session.id == session_id).first()
            if not row:
                return False
            db.delete(row)
            db.commit()
            return True
        finally:
            db.close()
    except Exception as e:
        logger.warning("Failed to delete session: %s", e)
        return False


def load_history(session_id: str) -> list[dict]:
    try:
        db = SessionLocal()
        try:
            rows = (
                db.query(Message)
                .filter(Message.session_id == session_id)
                .order_by(Message.id.asc())
                .limit(MAX_HISTORY)
                .all()
            )
            return [{"role": r.role, "content": r.content, "title": r.title} for r in rows]
        finally:
            db.close()
    except Exception as e:
        logger.warning("Failed to load history: %s", e)
        return []


def save_message(session_id: str, role: str, content: str, title: str = None):
    logger.info("save_message(session=%s, role=%s, content_len=%d)", session_id, role, len(content) if content else 0)
    db = None
    try:
        db = SessionLocal()
        msg = Message(session_id=session_id, role=role, content=content, title=title)
        db.add(msg)
        # 自动用第一条用户消息设置 session 标题
        if role == "user":
            existing = db.query(Message).filter(
                Message.session_id == session_id, Message.role == "user"
            ).count()
            if existing == 0:
                auto_title = content[:50] + ("..." if len(content) > 50 else "")
                db.query(Session).filter(Session.id == session_id).update(
                    {"title": auto_title, "updated_at": datetime.now()}
                )
        else:
            db.query(Session).filter(Session.id == session_id).update(
                {"updated_at": datetime.now()}
            )
        db.commit()
        logger.info("save_message 成功")
    except Exception as e:
        logger.error("save_message 失败: %s", e)
        import traceback
        logger.error(traceback.format_exc())
    finally:
        if db:
            db.close()
