from typing import Dict, Any, Optional
from .base import get_client, _to_dict


class DailyAttendanceController:
    """考勤记录与加班记录接口"""

    def __init__(self):
        self.client = get_client()

    def get_employee_attendance(self, employee_uuid: str, date: str) -> Dict:
        """获取员工某日的考勤记录"""
        response = self.client.get("/dailyAttendance", params={"employeeUuid": employee_uuid, "date": date})
        return _to_dict(response)

    def get_attendance_summary(self, date: str) -> Dict:
        """获取某日全体考勤汇总（出勤率、迟到、缺勤等）"""
        response = self.client.get("/dailyAttendance", params={"date": date})
        return _to_dict(response)

    def get_overtime_records(self, employee_uuid: str, start_date: str, end_date: str) -> Dict:
        """获取员工在日期范围内的加班记录（工时 > 8 小时）"""
        response = self.client.get("/dailyAttendance", params={
            "employeeUuid": employee_uuid,
            "startDate": start_date,
            "endDate": end_date
        })
        return _to_dict(response)
