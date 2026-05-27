from typing import Dict, Any, Optional
from .base import get_client, _to_dict


class DeptController:
    """部门管理接口"""

    def __init__(self):
        self.client = get_client()

    def list_departments(self) -> Dict:
        """获取部门列表"""
        response = self.client.get("/dept")
        return _to_dict(response)

    def get_department_details(self, dept_id: int) -> Dict:
        """获取部门详细信息"""
        response = self.client.get(f"/dept/{dept_id}")
        return _to_dict(response)

    def get_department_members(self, dept_id: int) -> Dict:
        """获取部门下的成员列表"""
        response = self.client.get(f"/dept/{dept_id}/members")
        return _to_dict(response)
