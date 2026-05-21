from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.core.llama_index import get_llm
from app.services.function_calling import get_available_tools

router = APIRouter(prefix="/chat", tags=["chat"])


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    reply: str
    tool_calls: list[str] = []


@router.post("", response_model=ChatResponse)
async def chat(req: ChatRequest):
    try:
        llm = get_llm()
        tools = get_available_tools()
        tool_map = {t.metadata.name: t for t in tools}

        response = llm.chat_with_tools(
            tool_map.keys(),
            user_msg=req.message,
        )

        called: list[str] = []
        for tool_name, tool_call in response.tool_calls or []:
            tool_fn = tool_map.get(tool_name)
            if tool_fn:
                result = tool_fn(**tool_call.tool_kwargs)
                called.append(f"{tool_name}: {result}")

        reply = response.message.content or ""
        return ChatResponse(reply=reply, tool_calls=called)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
