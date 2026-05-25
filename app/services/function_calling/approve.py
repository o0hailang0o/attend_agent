from typing import List, Optional
from llama_index.core.tools import FunctionTool
from app.services.attend_api.approve import ApproveController

def approve_list(employee_identifier: str = None) -> str:
    """获取待审批列表"""
    controller = ApproveController()
    try:
        result = controller.get_approval_list(employee_identifier)
        data = result.get('data', [])
        
        response = "待审批列表:\n"
        for item in data:
            response += f"- {item.get('employeeName', '未知')}: {item.get('type', '未知')} {item.get('date', '未知')}\n"
        
        return response
    except Exception as e:
        return f"获取待审批列表时出错: {str(e)}"

def approve_pass(application_id: int, comment: str = None) -> str:
    """审批通过"""
    controller = ApproveController()
    try:
        result = controller.approve_application(application_id, "已批准", comment)
        return f"申请 {application_id} 已批准"
    except Exception as e:
        return f"审批通过时出错: {str(e)}"

def approve_reject(application_id: int, comment: str) -> str:
    """审批驳回"""
    controller = ApproveController()
    try:
        result = controller.approve_application(application_id, "已驳回", comment)
        return f"申请 {application_id} 已驳回: {comment}"
    except Exception as e:
        return f"审批驳回时出错: {str(e)}"

__all__ = ["approve_list", "approve_pass", "approve_reject"]