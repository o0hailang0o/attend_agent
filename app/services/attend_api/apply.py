import httpx
from typing import Dict, Any, Optional
from app.core.config import settings

class ApplyController:
    def __init__(self):
        self.base_url = settings.attend_base_url or "http://localhost:8080"
        self.client = httpx.Client(base_url=self.base_url)
    
    def submit_leave_application(self, data: Dict) -> Dict:
        """提交请假申请"""
        response = self.client.post("/apply", json=data)
        return response.json()
    
    def get_leave_applications(self, employee_uuid: str = None, status: str = None) -> Dict:
        """获取请假申请列表"""
        params = {}
        if employee_uuid:
            params["employeeUuid"] = employee_uuid
        if status:
            params["status"] = status
        
        response = self.client.get("/apply", params=params)
        return response.json()