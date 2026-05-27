from typing import Dict, Any, Optional
from .base import get_client, _to_dict


class ApproveController:
    """审批操作接口（对接 attend GET /approve/my, PUT /approve/pass, PUT /approve/reject）"""

    def __init__(self):
        self.client = get_client()

    def get_approval_list(self, leader_uuid: str = None) -> Dict:
        """获取待审批列表

        Args:
            leader_uuid: 审批人 uuid，为空时调 GET /approve/my 查当前用户待审批
        """
        if leader_uuid:
            response = self.client.get("/approve", params={"leaderUuid": leader_uuid})
        else:
            response = self.client.get("/approve/my")
        return _to_dict(response)

    def approve_pass(self, approve_uuid: str) -> Dict:
        """审批通过

        Args:
            approve_uuid: 审批 uuid
        """
        response = self.client.put("/approve/pass", json={"uuid": approve_uuid})
        return _to_dict(response)

    def approve_reject(self, approve_uuid: str, reason: str) -> Dict:
        """驳回申请

        Args:
            approve_uuid: 审批 uuid
            reason: 驳回原因
        """
        response = self.client.put("/approve/reject", json={"uuid": approve_uuid, "reject": reason})
        return _to_dict(response)
