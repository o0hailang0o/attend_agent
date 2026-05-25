import httpx
from typing import Dict, Any, Optional
from app.core.config import settings

class DailyAttendanceController:
    def __init__(self):
        self.base_url = settings.attend_base_url or "http://localhost:8080"
        self.client = httpx.Client(base_url=self.base_url)
    
    def get_employee_attendance(self, employee_uuid: str, date: str) -> Dict:
        """获取员工某日的考勤记录"""
        response = self.client.get("/dailyAttendance", params={"employeeUuid": employee_uuid, "date": date})
        return response.json()
    
    def get_attendance_summary(self, date: str) -> Dict:
        """获取某日考勤汇总"""
        response = self.client.get("/dailyAttendance", params={"date": date})
        return response.json()
    
    def get_overtime_records(self, employee_uuid: str, start_date: str, end_date: str) -> Dict:
        """获取员工在日期范围内的加班记录"""
        response = self.client.get("/dailyAttendance", params={
            "employeeUuid": employee_uuid,
            "startDate": start_date,
            "endDate": end_date
        })
        return response.json()