from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from app.context import current_user_uuid
from app.services import agent_service

router = APIRouter(prefix="/sessions", tags=["sessions"])


class CreateSessionRequest(BaseModel):
    title: str = "新对话"


class RenameSessionRequest(BaseModel):
    title: str


class SessionResponse(BaseModel):
    id: str
    title: str
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


@router.get("", response_model=list[SessionResponse])
async def list_sessions_route():
    return agent_service.list_sessions(current_user_uuid.get())


@router.post("", response_model=SessionResponse)
async def create_session_route(req: CreateSessionRequest):
    session = agent_service.create_session(current_user_uuid.get(), req.title)
    if not session:
        raise HTTPException(status_code=500, detail="创建会话失败")
    return session


@router.put("/{session_id}", response_model=SessionResponse)
async def rename_session_route(session_id: str, req: RenameSessionRequest):
    ok = agent_service.rename_session(session_id, req.title)
    if not ok:
        raise HTTPException(status_code=404, detail="会话不存在")
    return agent_service.get_session(session_id)


@router.delete("/{session_id}")
async def delete_session_route(session_id: str):
    ok = agent_service.delete_session(session_id)
    if not ok:
        raise HTTPException(status_code=404, detail="会话不存在")
    return {"message": "已删除"}
