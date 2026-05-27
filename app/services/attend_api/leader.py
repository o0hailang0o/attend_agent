from typing import Dict, Any, Optional
from .base import get_client, _to_dict


class LeaderController:
    """领导列表接口"""

    def __init__(self):
        self.client = get_client()

    def list_leaders(self, dept: str = None) -> Dict:
        """获取领导列表

        Args:
            dept: 部门名称，为空时返回全部
        """
        params = {}
        if dept:
            params["dept"] = dept

        response = self.client.get("/leader", params=params)
        return _to_dict(response)

    def get_leader_details(self, leader_id: int) -> Dict:
        """获取领导详细信息"""
        response = self.client.get(f"/leader/{leader_id}")
        return _to_dict(response)
