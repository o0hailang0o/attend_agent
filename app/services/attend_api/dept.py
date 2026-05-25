import httpx
from typing import Dict, Any, Optional
from app.core.config import settings

class DeptController:
    def __init__(self):
        self.base_url = settings.attend_base_url or "http://localhost:8080"
        self.client = httpx.Client(base_url=self.base_url)
    
    def list_departments(self) -> Dict:
        """获取部门列表"""
        response = self.client.get("/dept")
        return response.json()
    
    def get_department_details(self, dept_id: int) -> Dict:
        """获取部门详细信息"""
        response = self.client.get(f"/dept/{dept_id}")
        return response.json()
    
    def get_department_members(self, dept_id: int) -> Dict:
        """获取部门成员"""
        response = self.client.get(f"/dept/{dept_id}/members")
        return response.json()