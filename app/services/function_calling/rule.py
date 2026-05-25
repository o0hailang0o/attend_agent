from typing import List, Optional
from llama_index.core.tools import FunctionTool
from app.services.attend_api.rule import RuleController

def list_rules() -> str:
    """获取考勤规则"""
    controller = RuleController()
    try:
        result = controller.get_attendance_rules()
        data = result.get('data', {})
        
        rules = data.get('rules', [])
        if not rules:
            return "未找到考勤规则"
        
        response = "考勤规则:\n"
        for rule in rules:
            response += f"- {rule.get('name', '未知')}: {rule.get('description', '无描述')}\n"
        
        return response
    except Exception as e:
        return f"获取考勤规则时出错: {str(e)}"

__all__ = ["list_rules"]