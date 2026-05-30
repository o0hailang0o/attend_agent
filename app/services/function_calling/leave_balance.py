import logging
from typing import Optional
from llama_index.core.tools import FunctionTool
from app.services.attend_api.leave_balance import LeaveBalanceController
from app.utils.user_lookup import resolve_user

logger = logging.getLogger(__name__)


def get_leave_balance(employee_identifier: str = "") -> str:
    """获取员工年假和调休假（公休假）余额

    调用 attend 接口 GET /leaveBalance/byUser?userUuid={uuid}，
    返回 Result<LeaveBalanceResp>。
    LeaveBalanceResp 字段：
    - annualRemainingHours: 年假剩余小时数
    - compRemainingHours: 调休假剩余小时数

    Args:
        employee_identifier: 员工姓名或工号。传空字符串时查当前登录用户

    Returns:
        成功时输出格式：
        "我来帮您查询{name}的假期余额。
         {name}的假期余额:
         - 年假剩余: X.X 小时
         - 调休假剩余: X.X 小时"
        未找到时返回："{name}暂无假期余额记录。"
        异常时返回："抱歉，查询假期余额时系统繁忙，请稍后重试。"
    """
    logger.info("get_leave_balance 传入参数: employee_identifier=%s", employee_identifier)
    controller = LeaveBalanceController()
    try:
        uuid = resolve_user(employee_identifier)
        logger.info("员工解析结果: %s -> %s", employee_identifier, uuid)
        if not uuid:
            return f"未找到员工「{employee_identifier}」，请确认姓名或工号是否正确。"
        thinking = f"我来帮您查询{employee_identifier}的假期余额。"
        logger.info("调用接口 GET /leaveBalance/byUser?userUuid=%s", uuid)
        result = controller.get_leave_balance_by_userUuid(uuid)
        data = result.get('data', {})
        if not data:
            return f"{thinking}\n{employee_identifier}暂无假期余额记录。"
        annual = data.get('annualRemainingHours', '0')
        comp = data.get('compRemainingHours', '0')
        return f"{thinking}\n{employee_identifier}的假期余额:\n- 年假剩余: {annual}小时\n- 调休假剩余: {comp}小时"
    except Exception as e:
        logger.error("get_leave_balance 出错: %s", str(e))
        return "抱歉，查询假期余额时系统繁忙，请稍后重试。"


__all__ = ["get_leave_balance"]
