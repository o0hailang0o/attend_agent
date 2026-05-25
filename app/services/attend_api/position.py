import httpx
from typing import Dict, Any, Optional
from app.core.config import settings

class PositionController:
    def __init__(self):
        self.base_url = settings.attend_base_url or "http://localhost:8080"
        self.client = httpx.Client(base_url=self.base_url)
    
    def list_positions(self, dept: str = None) -> Dict:
        """获取职位列表"""
        params = {}
        if dept:
            params["dept"] = dept
        
        response = self.client.get("/position", params=params)
        return response.json()
    
    def get_position_details(self, position_id: int) -> Dict:
        """获取职位详细信息"""
        response = self.client.get(f"/position/{position_id}")
        return response.json()