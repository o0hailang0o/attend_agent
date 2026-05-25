from typing import List, Optional
from llama_index.core.tools import FunctionTool
from app.services.attend_api.dept import DeptController

def list_departments() -> str:
    """获取部门列表"""
    controller = DeptController()
    try:
        result = controller.list_departments()
        data = result.get('data', [])
        
        if not data:
            return "未找到部门"
        
        response = "部门列表:\n"
        for dept in data:
            response += f"- {dept.get('name', '未知')}\n"
        
        return response
    except Exception as e:
        return f"获取部门列表时出错: {str(e)}"

__all__ = ["list_departments"]