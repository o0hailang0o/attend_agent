import logging, json, asyncio
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
from app.context import auth_token, current_user_uuid, get_pending, set_pending
from app.services.text_to_sql import text_to_sql as run_text_to_sql

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
    tools = {t.metadata.name: t for t in get_available_tools()}
    if name in tools:
        t = tools[name]
        if hasattr(t, "__call__"):
            logger.info("执行工具: %s params=%s", name, params)
            r = t(**params)
            return str(r) if not isinstance(r, str) else r
    return f"未找到工具: {name}"


def _build_messages(history: list[dict], system: str, user_msg: str, pending: dict | None = None) -> list[ChatMessage]:
    msgs = [ChatMessage(role=MessageRole.SYSTEM, content=system)]
    for h in history:
        if h.get("role") == "user":
            msgs.append(ChatMessage(role=MessageRole.USER, content=h["content"]))
        elif h.get("role") == "assistant":
            msgs.append(ChatMessage(role=MessageRole.ASSISTANT, content=h["content"]))
    # 如果有等待续接的工具调用，追加一条系统指令帮助 LLM 理解上下文
    if pending:
        pending_msg = (
            "【系统指令】你刚才正在为用户办理请假，已经收集了部分参数，但缺少以下信息："
            f"{pending.get('missing_text', '')}。"
            "用户现在提供了新的输入。如果用户的输入是缺失的某项参数值，你必须立即再次调用 register_leave，"
            "将之前已知的参数和用户新提供的参数一起传入，不要使用你的内部知识回答用户。"
        )
        msgs.append(ChatMessage(role=MessageRole.SYSTEM, content=pending_msg))
    msgs.append(ChatMessage(role=MessageRole.USER, content=user_msg))
    return msgs


def _handle_pending(pending: dict, user_msg: str) -> tuple[str, dict | None, list[str]]:
    """存在未完成的工具调用时，直接将用户输入合并到缺失参数中，绕过 LLM。

    必填参数依次为 leave_type, range, reason, leader，按顺序填入用户输入。
    返回: (tool_result, new_pending_or_none, [call_summary_str])
    """
    tool_name = pending["tool"]
    prev_params = dict(pending.get("params", {}))

    # 如果是确认等待状态，用户说"确认/提交/是的/可以"等 → 直接提交
    if pending.get("status") == "confirming":
        confirming_keywords = ["确认", "提交", "是的", "可以", "好", "行", "对", "没错", "ok", "yes", "确定"]
        user_lower = user_msg.strip().lower()
        if any(kw in user_lower for kw in confirming_keywords):
            prev_params["confirmed"] = True
            result = _execute_tool(tool_name, prev_params)
            return result, None, [f"[{tool_name}] {result}"]
        else:
            # 用户说了别的内容，取消确认等待，交给 LLM
            return pending.get("result", ""), None, []

    user_input = user_msg.strip()

    for param_name in ["leave_type", "range", "reason", "leader"]:
        if not prev_params.get(param_name):
            prev_params[param_name] = user_input
            break

    result = _execute_tool(tool_name, prev_params)
    call_summary = f"[{tool_name}] {result}"

    new_pending = None
    if result.strip().startswith("还需要提供以下信息"):
        missing_lines = [l.strip().lstrip("- ") for l in result.split("\n") if l.strip().startswith("-")]
        missing_text = "、".join(missing_lines) if missing_lines else "部分参数"
        new_pending = {"tool": tool_name, "params": prev_params, "missing_text": missing_text, "result": result}
    elif result.strip().startswith("请假单确认"):
        # 参数齐全，等待用户确认 → 保存完整参数以便确认时直接提交
        new_pending = {"tool": tool_name, "params": prev_params, "result": result, "status": "confirming"}

    return result, new_pending, [call_summary]


_PENDING_TOOLS = {"register_leave"}


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

        # 读取并清除等待续接的工具调用
        pending = get_pending(user_uuid)

        master_llm = get_llm()

        # ---- function calling 与 text_to_sql 并行 ----
        new_pending = None

        if pending and pending.get("tool") in _PENDING_TOOLS:
            # 请假流程中，跳过 text_to_sql，只处理参数续接
            sql_result = ""
            try:
                fc_reply, new_pending, called = _handle_pending(pending, req.message)
                tool_calls = []
                results = [fc_reply]
            except Exception as e:
                logger.error("_handle_pending 异常: %s", e)
                fc_reply = "抱歉，系统处理请求时遇到问题，请稍后重试。"
                tool_calls = []
                results = []
                called = []
        else:
            sql_task = asyncio.to_thread(run_text_to_sql, req.message, user_uuid)
            try:
                local_llm = get_llm()
                r = local_llm.chat(_build_messages(history, SYSTEM_PROMPT, req.message, pending))
                text = (r.message.content or "").strip()
                tcs = _parse_tool_calls(text)
                res_list = []
                cal_list = []
                for tc in tcs:
                    name = tc.get("tool", "")
                    params = tc.get("params", {})
                    try:
                        result = _execute_tool(name, params)
                    except Exception as e:
                        logger.warning("工具 %s 执行异常: %s", name, e)
                        result = f"工具 {name} 执行出错: {e}"
                    cal_list.append(f"[{name}] {result}")
                    res_list.append(f"工具【{name}】结果: {result}")
                    if result.strip().startswith("还需要提供以下信息"):
                        missing_lines = [l.strip().lstrip("- ") for l in result.split("\n") if l.strip().startswith("-")]
                        missing_text = "、".join(missing_lines) if missing_lines else "部分参数"
                        new_pending = {"tool": name, "params": params, "missing_text": missing_text, "result": result}
                fc_reply, tool_calls, results, called = text, tcs, res_list, cal_list
            except Exception as e:
                logger.error("function_calling 异常: %s", e)
                fc_reply = "抱歉，系统处理请求时遇到问题，请稍后重试。"
                tool_calls = []
                results = []
                called = []

            sql_result = ""
            try:
                sql_result = await sql_task
            except Exception as e:
                logger.warning("text-to-sql 异常: %s", e)
            if isinstance(sql_result, BaseException):
                sql_result = ""
            logger.info("text-to-sql 结果: %s", "有数据" if sql_result else "为空")

        if new_pending:
            set_pending(user_uuid, new_pending)

        # ---- 合成最终回复 ----
        if tool_calls or sql_result:
            all_results = list(results)
            if sql_result:
                all_results.append(sql_result)

            final_prompt = TOOL_RESULT_PROMPT.format(question=req.message, results="\n".join(all_results))
            try:
                final = master_llm.chat(_build_messages(history, RESULT_SYSTEM_PROMPT, final_prompt))
                reply = (final.message.content or "").strip()
            except Exception as e:
                logger.error("master_llm 合成失败: %s", e)
                reply = fc_reply or ""
        else:
            reply = fc_reply

        if not reply:
            reply = _mock_chat(req.message)

        logger.info("准备保存消息: session_id=%s, user_uuid=%s, reply_len=%d", session_id, user_uuid, len(reply) if reply else 0)
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
