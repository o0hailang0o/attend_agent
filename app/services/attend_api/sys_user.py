from typing import List, Dict, Optional
from .base import get_client, _to_dict


class SysUserController:
    """员工信息接口"""

    def __init__(self):
        self.client = get_client()

    def get_user_by_account(self, account: str) -> Dict:
        """根据账号获取用户信息"""
        response = self.client.get(f"/sysuser/byAccount", params={"account": account})
        return _to_dict(response)

    def get_user_by_work_num(self, work_num: str) -> Dict:
        """根据工号获取用户信息"""
        response = self.client.get(f"/sysuser/byWorkNum", params={"work_num": work_num})
        return _to_dict(response)

    def get_user_by_name(self, name: str) -> Dict:
        """根据姓名获取用户信息"""
        response = self.client.get(f"/sysuser/byName", params={"name": name})
        return _to_dict(response)

    def list_users(self, page: int = 1, size: int = 10) -> Dict:
        """获取用户列表（分页）"""
        response = self.client.get(f"/sysuser/list", params={"page": page, "size": size})
        return _to_dict(response)

    def search_users(self, name: str) -> List[Dict]:
        """搜索用户（模糊匹配）"""
        response = self.client.get(f"/sysuser", params={"name": name})
        data = _to_dict(response)
        return data if isinstance(data, list) else data.get("data", []) if isinstance(data, dict) else []

    def get_user_details(self, user_id: int) -> Dict:
        """获取用户详细信息"""
        response = self.client.get(f"/sysuser/{user_id}")
        return _to_dict(response)
