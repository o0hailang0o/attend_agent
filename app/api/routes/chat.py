from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.core.config import settings
from app.core.llama_index import get_llm
from app.services.function_calling import get_available_tools

router = APIRouter(prefix="/chat", tags=["chat"])


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    reply: str
    tool_calls: list[str] = []


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


@router.post("", response_model=ChatResponse)
async def chat(req: ChatRequest):
    if not settings.llm_api_key:
        return ChatResponse(reply=_mock_chat(req.message))

    try:
        llm = get_llm()
        tools = list(get_available_tools())
        tool_map = {t.metadata.name: t for t in tools}

        response = llm.chat_with_tools(
            tools,
            user_msg=req.message,
        )

        called: list[str] = []
        if hasattr(response, "tool_calls") and response.tool_calls:
            for tc in response.tool_calls:
                tool_name = tc.tool_name
                tool_fn = tool_map.get(tool_name)
                if tool_fn:
                    result = tool_fn(**tc.tool_kwargs)
                    called.append(f"{tool_name}: {result}")

        reply = response.message.content or ""
        return ChatResponse(reply=reply, tool_calls=called)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
