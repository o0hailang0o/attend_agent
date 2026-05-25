from typing import List, Optional
from llama_index.core.tools import FunctionTool
from app.services.attend_api.sys_user import SysUserController

def search_user(name: str) -> str:
    """根据姓名搜索员工"""
    controller = SysUserController()
    try:
        result = controller.search_users(name)
        if not result:
            return f"未找到姓名包含 '{name}' 的员工"
        
        users = result.get('data', []) if isinstance(result, dict) else result
        if not users:
            return f"未找到姓名包含 '{name}' 的员工"
        
        response = f"找到 {len(users)} 名包含 '{name}' 的员工:\n"
        for user in users:
            response += f"- {user.get('name', '未知')} (工号: {user.get('work_num', '未知')}, 部门: {user.get('dept', '未知')})\n"
        
        return response
    except Exception as e:
        return f"搜索员工时出错: {str(e)}"

__all__ = ["search_user"]