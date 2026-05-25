from typing import List, Optional
from llama_index.core.tools import FunctionTool
from app.services.attend_api.apply import ApplyController

def register_leave(employee_identifier: str, leave_type: str, start_date: str, end_date: str, reason: str) -> str:
    """提交请假申请"""
    controller = ApplyController()
    try:
        # 简化处理，假设employee_identifier就是employee_uuid
        data = {
            "employeeUuid": employee_identifier,
            "leaveType": leave_type,
            "startDate": start_date,
            "endDate": end_date,
            "reason": reason
        }
        result = controller.submit_leave_application(data)
        return f"请假申请已提交，申请ID: {result.get('data', {}).get('applicationId', '未知')}"
    except Exception as e:
        return f"提交请假申请时出错: {str(e)}"

def get_leave_balance(employee_identifier: str) -> str:
    """获取员工假期余额"""
    controller = ApplyController()
    try:
        # 简化处理，这里应该使用LeaveBalanceController
        # 暂时使用ApplyController作为示例
        result = controller.get_leave_applications(employee_identifier)
        data = result.get('data', [])
        approved_leaves = [l for l in data if l.get('status') == '已批准']
        total_days = len(approved_leaves)
        return f"员工 {employee_identifier} 的假期余额: 总计 {total_days} 天"
    except Exception as e:
        return f"获取假期余额时出错: {str(e)}"

__all__ = ["register_leave", "get_leave_balance"]