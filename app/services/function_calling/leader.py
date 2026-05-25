from typing import List, Optional
from llama_index.core.tools import FunctionTool
from app.services.attend_api.leader import LeaderController

def list_leaders(dept: str = None) -> str:
    """获取领导列表"""
    controller = LeaderController()
    try:
        result = controller.list_leaders(dept)
        data = result.get('data', [])
        
        if not data:
            return "未找到领导"
        
        response = "领导列表:\n"
        for leader in data:
            response += f"- {leader.get('name', '未知')} ({leader.get('position', '未知')}, 部门: {leader.get('dept', '未知')})\n"
        
        return response
    except Exception as e:
        return f"获取领导列表时出错: {str(e)}"

__all__ = ["list_leaders"]