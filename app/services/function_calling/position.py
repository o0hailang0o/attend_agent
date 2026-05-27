import logging
from typing import List, Optional
from llama_index.core.tools import FunctionTool
from app.services.attend_api.position import PositionController

logger = logging.getLogger(__name__)

def list_positions() -> str:
    """获取职位列表

    调用 attend 接口 GET /position，返回 Result<List<PositionResp>>。
    PositionResp 字段：
    - id: 主键
    - uuid: 职位uuid
    - name: 职位名称

    Args:
        无参数

    Returns:
        成功时输出格式：
        "我来帮您查询职位列表。
         共 N 个职位:
         - {name}"
        无数据时返回："未找到职位信息。"
        异常时返回："抱歉，查询职位列表时系统繁忙，请稍后重试。"
    """
    logger.info("list_positions 被调用")
    controller = PositionController()
    try:
        thinking = "我来帮您查询职位列表。"
        logger.info("调用接口 GET /position")
        result = controller.list_positions()
        data = result.get('data', [])

        if not data:
            return f"{thinking}\n未找到职位信息。"

        lines = "\n".join(f"- {position.get('name', '未知')}" for position in data)
        return f"{thinking}\n共 {len(data)} 个职位:\n{lines}"
    except Exception as e:
        logger.error("list_positions 出错: %s", str(e))
        return "抱歉，查询职位列表时系统繁忙，请稍后重试。"

__all__ = ["list_positions"]
