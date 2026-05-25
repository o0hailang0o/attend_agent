import httpx
from typing import Dict, Any, Optional
from app.core.config import settings

class RuleController:
    def __init__(self):
        self.base_url = settings.attend_base_url or "http://localhost:8080"
        self.client = httpx.Client(base_url=self.base_url)
    
    def get_attendance_rules(self) -> Dict:
        """获取考勤规则"""
        response = self.client.get("/rule")
        return response.json()
    
    def get_rule_details(self, rule_id: int) -> Dict:
        """获取规则详细信息"""
        response = self.client.get(f"/rule/{rule_id}")
        return response.json()