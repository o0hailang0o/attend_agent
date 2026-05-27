from typing import Dict, Any, Optional
from .base import get_client, _to_dict


class RuleController:
    """考勤规则接口"""

    def __init__(self):
        self.client = get_client()

    def get_attendance_rules(self) -> Dict:
        """获取考勤规则列表"""
        response = self.client.get("/rule")
        return _to_dict(response)

    def get_rule_details(self, rule_id: int) -> Dict:
        """获取考勤规则详细信息"""
        response = self.client.get(f"/rule/{rule_id}")
        return _to_dict(response)
