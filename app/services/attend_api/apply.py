from typing import Dict, Any, Optional
from .base import get_client, _to_dict
from app.utils.attend_code_converter import LeaveTypeConverter


def map_leave_type(name: str) -> int:
    return LeaveTypeConverter.to_code(name) or 2


class ApplyController:
    """考勤申请接口（对接 attend POST /apply, GET /apply）"""

    def __init__(self):
        self.client = get_client()

    def submit_leave_application(self, data: Dict) -> Dict:
        """提交请假申请

        字段映射到 ApplyReq (camelCase)：
        - month:startTime当前月的1日 比如2025-05-24 17：56   month就等于2025-05-01
        - type: 申请类型（Integer，见 map_leave_type）
        - startTime: 开始时间（LocalDateTime, "yyyy-MM-ddTHH:mm:ss"）
        - endTime: 结束时间（LocalDateTime）
        - reason: 请假事由
        - applyUserUuid: 申请人 uuid
        - leaderUuid: 审批人 uuid（可选）

        Args:
            data: 包含 type/startTime/endTime/reason/applyUserUuid 的字典
        """
        response = self.client.post("/apply", json=data)
        return _to_dict(response)

    def get_leave_applications(self, user_uuid: str = None) -> Dict:
        """获取请假申请列表

        Args:
            user_uuid: 申请人 uuid，为空时查当前用户
        """
        params = {"page": 1, "size": 50}
        if user_uuid:
            params["userUuid"] = user_uuid
        response = self.client.get("/apply", params=params)
        return _to_dict(response)
