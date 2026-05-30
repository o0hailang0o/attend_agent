import logging
from typing import List, Optional
from llama_index.core.tools import FunctionTool
from app.services.attend_api.door_access import DoorAccessController
from app.utils.user_lookup import resolve_user
from app.utils.date_converter import DateConverter

logger = logging.getLogger(__name__)

def get_door_access(employee_identifier: str = "", date: str = "") -> str:
    """获取员工某日的门禁开门记录（打卡记录或出入记录）

    支持自然语言日期（今天、昨天、周一、5月11日），自动解析后查询。
    返回结果包含开门时间和地点信息。

    Args:
        employee_identifier: 员工姓名或工号，如果是空就是本人
        date: 日期，支持自然语言（今天、昨天、周一、5月11日等）如果是空就是今天
    return:
        accessDatetime: 门禁出入时间，YYYY-MM-DD HH:mm:ss
        doorNo：门号
        direction：进出 0==进入 1==离开
    """
    logger.info("get_door_access 传入参数: employee_identifier=%s, date=%s", employee_identifier, date)
    controller = DoorAccessController()
    try:
        uuid = resolve_user(employee_identifier)
        logger.info("员工解析结果: %s -> %s", employee_identifier, uuid)
        if not uuid:
            return f"未找到员工「{employee_identifier}」，请确认姓名或工号是否正确。"
        if date:
            parsed = DateConverter.parse_date_to_string(date)
        else:    
            parsed = DateConverter.parse_date_to_string("今天")
        date_str = parsed if parsed else date
        logger.info("日期解析结果: %s -> %s", date, date_str)
        thinking = f"我来帮您查询{employee_identifier}在{date_str}的门禁记录。"
        logger.info("调用接口 GET /doorAccess?employeeUuid=%s&date=%s", uuid, date_str)
        result = controller.get_door_access_records(uuid, date_str)
        data = result.get('data', [])
        if not data:
            return f"{thinking}\n{employee_identifier}在{date_str}没有门禁记录。"

        lines = "\n".join(f"- {r.get('accessDatetime', '未知')} - {r.get('direction', '未知')}-{r.get('direction', '未知')}"
                          for r in data)
        return f"{thinking}\n查询到以下门禁记录:\n{lines}"
    except Exception as e:
        logger.error("get_door_access 出错: %s", str(e))
        return "抱歉，查询门禁记录时系统繁忙，请稍后重试。"

__all__ = ["get_door_access"]
