from typing import List, Optional
from llama_index.core.tools import FunctionTool
from app.services.attend_api.position import PositionController

def list_positions(dept: str = None) -> str:
    """获取职位列表"""
    controller = PositionController()
    try:
        result = controller.list_positions(dept)
        data = result.get('data', [])
        
        if not data:
            return "未找到职位"
        
        response = "职位列表:\n"
        for position in data:
            response += f"- {position.get('name', '未知')} (部门: {position.get('dept', '未知')})\n"
        
        return response
    except Exception as e:
        return f"获取职位列表时出错: {str(e)}"

__all__ = ["list_positions"]