import logging, json
from fastapi import APIRouter, HTTPException, Request, Query
from pydantic import BaseModel, Field
from llama_index.core.llms import ChatMessage, MessageRole
from typing import Optional

from app.core.config import settings
from app.core.llama_index import get_llm
from app.core.prompts import SYSTEM_PROMPT, RESULT_SYSTEM_PROMPT, TOOL_RESULT_PROMPT
from app.services.function_calling import get_available_tools
from app.services.chat_memory import load_history, save_message
from app.services import agent_service
from app.context import auth_token, current_user_uuid

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    reply: str
    tool_calls: list[str] = []


class MessageResponse(BaseModel):
    role: str
    content: str
    title: Optional[str] = None


MOCK_RULES = [
    (["出勤", "打卡", "考勤率", "出勤率"], "今日出勤率 96.7%，已出勤 115 人，迟到 6 人，缺勤 3 人，请假 4 人，整体情况良好。"),
    (["迟到"], "今日共有 6 人迟到，主要集中在产品研发部和市场部。本月累计迟到 23 人次。"),
    (["缺勤"], "今日有 3 人缺勤，本月累计缺勤 8 人次。"),
    (["请假", "休假", "年假", "调休"], "目前有 4 位同事正在休假。您可以在左侧「请假申请」页面提交请假申请，或查看个人假期余额。"),
    (["加班"], "如需查询加班记录，请提供员工编号和日期范围。"),
    (["你好", "您好", "在吗", "hello", "hi"], "你好！我是考勤小助手，可以帮你查询出勤统计、迟到缺勤情况、请假和加班记录。请问你想了解什么？"),
]


def _mock_chat(message: str) -> str:
    for keywords, reply in MOCK_RULES:
        if any(k in message for k in keywords):
            return reply
    return (
        "我是考勤小助手，可以查询以下信息：\n"
        "• 今日出勤统计（出勤率、迟到、缺勤、请假人数）\n"
        "• 本月迟到/缺勤汇总\n"
        "• 请假申请和假期余额\n"
        "• 加班记录查询\n\n"
        "请问你想了解什么？"
    )


def _parse_tool_calls(text: str) -> list[dict]:
    calls = []
    for line in text.strip().split("\n"):
        line = line.strip()
        if line.startswith("TOOL_CALL:"):
            json_str = line[len("TOOL_CALL:"):].strip()
            try:
                obj = json.loads(json_str)
                if isinstance(obj, dict):
                    calls.append(obj)
            except json.JSONDecodeError:
                logger.warning("无法解析工具调用: %s", json_str)
    return calls


def _execute_tool(name: str, params: dict) -> str:
    tools = list(get_available_tools())
    for t in tools:
        if t.metadata.name == name:
            logger.info("执行工具: %s params=%s", name, params)
            return t(**params)
    return f"未找到工具: {name}"


def _build_messages(history: list[dict], system: str, user_msg: str) -> list[ChatMessage]:
    msgs = [ChatMessage(role=MessageRole.SYSTEM, content=system)]
    for h in history:
        if h.get("role") == "user":
            msgs.append(ChatMessage(role=MessageRole.USER, content=h["content"]))
        elif h.get("role") == "assistant":
            msgs.append(ChatMessage(role=MessageRole.ASSISTANT, content=h["content"]))
    msgs.append(ChatMessage(role=MessageRole.USER, content=user_msg))
    return msgs


@router.post("", response_model=ChatResponse)
async def chat(req: ChatRequest):
    if not settings.llm_api_key:
        return ChatResponse(reply=_mock_chat(req.message))

    user_uuid = current_user_uuid.get()
    try:
        session_id = req.session_id
        if session_id:
            history = agent_service.load_history(session_id)
        else:
            history = await load_history(user_uuid)

        llm = get_llm()
        r = llm.chat(_build_messages(history, SYSTEM_PROMPT, req.message))
        reply_text = (r.message.content or "").strip()

        called = []
        tool_calls = _parse_tool_calls(reply_text)

        if tool_calls:
            results = []
            for tc in tool_calls:
                name = tc.get("tool", "")
                params = tc.get("params", {})
                result = _execute_tool(name, params)
                called.append(f"[{name}] {result}")
                results.append(f"工具【{name}】结果: {result}")

            # 将工具调用信息存入历史，供下一轮 LLM 参考
            for tc in tool_calls:
                name = tc.get("tool", "")
                params = tc.get("params", {})
                record = f"【系统调用工具】{name}，参数：{json.dumps(params, ensure_ascii=False)}"
                if session_id:
                    agent_service.save_message(session_id, "assistant", record)
                else:
                    await save_message(user_uuid, "assistant", record)
            for r in results:
                if session_id:
                    agent_service.save_message(session_id, "assistant", r)
                else:
                    await save_message(user_uuid, "assistant", r)

            final_prompt = TOOL_RESULT_PROMPT.format(question=req.message, results="\n".join(results))
            final = llm.chat(_build_messages(history, RESULT_SYSTEM_PROMPT, final_prompt))
            reply = (final.message.content or "").strip()
        else:
            reply = reply_text

        if not reply:
            reply = _mock_chat(req.message)

        if session_id:
            agent_service.save_message(session_id, "user", req.message)
            agent_service.save_message(session_id, "assistant", reply)
        else:
            await save_message(user_uuid, "user", req.message)
            await save_message(user_uuid, "assistant", reply)

        return ChatResponse(reply=reply, tool_calls=called)

    except Exception as e:
        logger.error("chat error: %s", str(e))
        return ChatResponse(reply="抱歉，系统暂时无法处理该请求，请稍后重试。")


@router.get("/history", response_model=list[MessageResponse])
async def chat_history_route(session_id: str = Query(...)):
    return agent_service.load_history(session_id)
