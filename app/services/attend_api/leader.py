import httpx
from typing import Dict, Any, Optional
from app.core.config import settings

class LeaderController:
    def __init__(self):
        self.base_url = settings.attend_base_url or "http://localhost:8080"
        self.client = httpx.Client(base_url=self.base_url)
    
    def list_leaders(self, dept: str = None) -> Dict:
        """获取领导列表"""
        params = {}
        if dept:
            params["dept"] = dept
        
        response = self.client.get("/leader", params=params)
        return response.json()
    
    def get_leader_details(self, leader_id: int) -> Dict:
        """获取领导详细信息"""
        response = self.client.get(f"/leader/{leader_id}")
        return response.json()