from typing import Dict, Any, Optional
from .base import get_client, _to_dict


class DoorAccessController:
    """门禁开门记录接口"""

    def __init__(self):
        self.client = get_client()

    def get_door_access_records(self, employee_uuid: str, date: str) -> Dict:
        """获取员工某日的门禁开门记录（打卡记录或出入记录）

        Args:
            employee_uuid: 员工 UUID
            date: 日期，格式 YYYY-MM-DD
        """
        response = self.client.get("/doorAccess", params={
            "employeeUuid": employee_uuid,
            "date": date
        })
        return _to_dict(response)

    def get_door_access_by_time_range(self, employee_uuid: str, start_time: str, end_time: str) -> Dict:
        """获取员工在时间范围内的门禁开门记录"""
        response = self.client.get("/doorAccess", params={
            "employeeUuid": employee_uuid,
            "startTime": start_time,
            "endTime": end_time
        })
        return _to_dict(response)
