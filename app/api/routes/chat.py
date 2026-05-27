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
from app.context import auth_token, current_user_uuid, pending_tool_call
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
    tools = list(get_available_tools())
    for t in tools:
        if t.metadata.name == name:
            logger.info("执行工具: %s params=%s", name, params)
            return t(**params)
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
        pending = pending_tool_call.get()
        pending_tool_call.set(None)

        master_llm = get_llm()

        # ---- 两个线程并行（asyncio.gather 实现类似 Java join） ----
        def _run_function_calling():
            """线程中执行：LLM 调用 + 工具执行，返回结果"""
            local_llm = get_llm()
            r = local_llm.chat(_build_messages(history, SYSTEM_PROMPT, req.message, pending))
            text = (r.message.content or "").strip()
            tcs = _parse_tool_calls(text)
            res_list = []
            cal_list = []
            new_pending = None
            for tc in tcs:
                name = tc.get("tool", "")
                params = tc.get("params", {})
                result = _execute_tool(name, params)
                cal_list.append(f"[{name}] {result}")
                res_list.append(f"工具【{name}】结果: {result}")
                if result.strip().startswith("还需要提供以下信息"):
                    missing_lines = [l.strip().lstrip("- ") for l in result.split("\n") if l.strip().startswith("-")]
                    missing_text = "、".join(missing_lines) if missing_lines else "部分参数"
                    new_pending = {"tool": name, "params": params, "missing_text": missing_text, "result": result}
            return text, tcs, res_list, cal_list, new_pending

        fc_task = asyncio.create_task(asyncio.to_thread(_run_function_calling))
        sql_task = asyncio.create_task(asyncio.to_thread(run_text_to_sql, req.message))

        fc_result = None
        sql_result = ""
        try:
            fc_result = await asyncio.wait_for(fc_task, timeout=35)
        except asyncio.TimeoutError:
            logger.error("function_calling 超时（35秒）")
            return ChatResponse(reply="系统处理超时，请稍后再试")
        except Exception as e:
            logger.error("function_calling 异常: %s", e)
            return ChatResponse(reply="系统处理出错，请稍后再试")

        fc_reply, tool_calls, results, called, new_pending = fc_result

        if new_pending:
            pending_tool_call.set(new_pending)

        # text-to-sql 已在后台并行运行，给它额外时间完成
        try:
            sql_result = await asyncio.wait_for(sql_task, timeout=10)
        except asyncio.TimeoutError:
            logger.info("text-to-sql 超过 10 秒未完成，跳过")
            sql_result = ""
        except Exception as e:
            logger.warning("text-to-sql 异常: %s", e)
            sql_result = ""
        if isinstance(sql_result, BaseException):
            sql_result = ""
        logger.info("text-to-sql 结果 (%s): %s", "有数据" if sql_result else "为空", sql_result[:100] if sql_result else "")

        # ---- 合成最终回复 ----
        if tool_calls:
            all_results = list(results)
            if sql_result:
                all_results.append(sql_result)

            for tc in tool_calls:
                name = tc.get("tool", "")
                params = tc.get("params", {})
                record = f"【系统调用工具】{name}，参数：{json.dumps(params, ensure_ascii=False)}"
                if session_id:
                    agent_service.save_message(session_id, "assistant", record)
                else:
                    await save_message(user_uuid, "assistant", record)
            for r in all_results:
                if session_id:
                    agent_service.save_message(session_id, "assistant", r)
                else:
                    await save_message(user_uuid, "assistant", r)

            final_prompt = TOOL_RESULT_PROMPT.format(question=req.message, results="\n".join(all_results))
            try:
                final = master_llm.chat(_build_messages(history, RESULT_SYSTEM_PROMPT, final_prompt))
                reply = (final.message.content or "").strip()
            except Exception as e:
                logger.error("master_llm 合成失败: %s", e)
                reply = fc_reply or ""
        else:
            reply = fc_reply
            if sql_result:
                reply += "\n\n" + sql_result

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
