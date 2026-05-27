import logging
from typing import List, Optional
from llama_index.core.tools import FunctionTool
from app.services.attend_api.leader import LeaderController

logger = logging.getLogger(__name__)

def list_leaders() -> str:
    """获取领导列表

    调用 attend 接口 GET /leader，返回 Result<List<LeaderResp>>。
    LeaderResp 字段：
    - id: 主键
    - leaderUuid: 领导用户uuid
    - leaderName: 领导姓名
    - parentId: 上级领导id
    - level: 级别
    - tree: 审批链

    Args:
        无参数

    Returns:
        成功时输出格式：
        "我来帮您查询领导列表。
         领导列表（共 N 人）:
         - {leaderName}（级别: {level}）"
        无数据时返回："未找到领导信息。"
        异常时返回："抱歉，查询领导列表时系统繁忙，请稍后重试。"
    """
    logger.info("list_leaders 被调用")
    controller = LeaderController()
    try:
        thinking = "我来帮您查询领导列表。"
        logger.info("调用接口 GET /leader")
        result = controller.list_leaders()
        data = result.get('data', [])

        if not data:
            return f"{thinking}\n未找到领导信息。"

        lines = "\n".join(
            f"- {leader.get('leaderName', '未知')}（级别: {leader.get('level', '未知')}）"
            for leader in data
        )
        return f"{thinking}\n领导列表（共 {len(data)} 人）:\n{lines}"
    except Exception as e:
        logger.error("list_leaders 出错: %s", str(e))
        return "抱歉，查询领导列表时系统繁忙，请稍后重试。"

__all__ = ["list_leaders"]
