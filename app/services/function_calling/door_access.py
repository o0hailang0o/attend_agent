from typing import List, Optional
from llama_index.core.tools import FunctionTool
from app.services.attend_api.door_access import DoorAccessController

def get_door_access(employee_identifier: str, date: str) -> str:
    """获取员工某日的门禁记录"""
    controller = DoorAccessController()
    try:
        # 简化处理，假设employee_identifier就是employee_uuid
        result = controller.get_door_access_records(employee_identifier, date)
        data = result.get('data', [])
        if not data:
            return f"员工 {employee_identifier} 在 {date} 没有门禁记录"
        
        response = f"员工 {employee_identifier} 在 {date} 的门禁记录:\n"
        for record in data:
            response += f"- {record.get('accessTime', '未知')} - {record.get('location', '未知')}\n"
        
        return response
    except Exception as e:
        return f"获取门禁记录时出错: {str(e)}"

__all__ = ["get_door_access"]