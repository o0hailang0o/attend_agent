import logging
from typing import List, Optional
from llama_index.core.tools import FunctionTool
from app.services.attend_api.dept import DeptController

logger = logging.getLogger(__name__)

def list_departments() -> str:
    """获取部门列表

    调用 attend 接口 GET /dept，返回 Result<List<DeptResp>>。
    DeptResp 字段：
    - id: 主键
    - uuid: 部门uuid
    - name: 部门名称
    - parentUuid: 上级部门uuid

    Args:
        无参数

    Returns:
        成功时输出格式：
        "我来帮您查询部门列表。
         共 N 个部门:
         - {name}"
        无数据时返回："未找到部门信息。"
        异常时返回："抱歉，查询部门列表时系统繁忙，请稍后重试。"
    """
    logger.info("list_departments 被调用")
    controller = DeptController()
    try:
        thinking = "我来帮您查询部门列表。"
        logger.info("调用接口 GET /dept")
        result = controller.list_departments()
        data = result.get('data', [])

        if not data:
            return f"{thinking}\n未找到部门信息。"

        lines = "\n".join(f"- {dept.get('name', '未知')}" for dept in data)
        return f"{thinking}\n共 {len(data)} 个部门:\n{lines}"
    except Exception as e:
        logger.error("list_departments 出错: %s", str(e))
        return "抱歉，查询部门列表时系统繁忙，请稍后重试。"

__all__ = ["list_departments"]
