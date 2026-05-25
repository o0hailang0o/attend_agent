import httpx
from typing import Dict, Any, Optional
from app.core.config import settings

class ApproveController:
    def __init__(self):
        self.base_url = settings.attend_base_url or "http://localhost:8080"
        self.client = httpx.Client(base_url=self.base_url)
    
    def get_approval_list(self, employee_uuid: str = None, status: str = None) -> Dict:
        """获取审批列表"""
        params = {}
        if employee_uuid:
            params["employeeUuid"] = employee_uuid
        if status:
            params["status"] = status
        
        response = self.client.get("/approve", params=params)
        return response.json()
    
    def approve_application(self, application_id: int, status: str, comment: str = None) -> Dict:
        """审批申请"""
        data = {
            "status": status,
            "comment": comment
        }
        response = self.client.put(f"/approve/{application_id}", json=data)
        return response.json()