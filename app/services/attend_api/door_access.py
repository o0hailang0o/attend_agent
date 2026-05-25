import httpx
from typing import Dict, Any, Optional
from app.core.config import settings

class DoorAccessController:
    def __init__(self):
        self.base_url = settings.attend_base_url or "http://localhost:8080"
        self.client = httpx.Client(base_url=self.base_url)
    
    def get_door_access_records(self, employee_uuid: str, date: str) -> Dict:
        """获取员工某日的门禁记录"""
        response = self.client.get("/doorAccess", params={
            "employeeUuid": employee_uuid,
            "date": date
        })
        return response.json()
    
    def get_door_access_by_time_range(self, employee_uuid: str, start_time: str, end_time: str) -> Dict:
        """获取员工在时间范围内的门禁记录"""
        response = self.client.get("/doorAccess", params={
            "employeeUuid": employee_uuid,
            "startTime": start_time,
            "endTime": end_time
        })
        return response.json()