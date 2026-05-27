from typing import Dict, Any, Optional
from .base import get_client, _to_dict


class PositionController:
    """职位管理接口"""

    def __init__(self):
        self.client = get_client()

    def list_positions(self, dept: str = None) -> Dict:
        """获取职位列表

        Args:
            dept: 部门名称，为空时返回全部
        """
        params = {}
        if dept:
            params["dept"] = dept

        response = self.client.get("/position", params=params)
        return _to_dict(response)

    def get_position_details(self, position_id: int) -> Dict:
        """获取职位详细信息"""
        response = self.client.get(f"/position/{position_id}")
        return _to_dict(response)
