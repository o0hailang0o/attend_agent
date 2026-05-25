import httpx
from typing import List, Dict, Optional
from app.core.config import settings

class SysUserController:
    def __init__(self):
        self.base_url = settings.attend_base_url or "http://localhost:8080"
        self.client = httpx.Client(base_url=self.base_url)
    
    def get_user_by_account(self, account: str) -> Dict:
        """根据工号获取用户信息"""
        response = self.client.get(f"/sysuser/byAccount", params={"account": account})
        return response.json()
    
    def get_user_by_work_num(self, work_num: str) -> Dict:
        """根据工号获取用户信息"""
        response = self.client.get(f"/sysuser/byWorkNum", params={"work_num": work_num})
        return response.json()
    
    def get_user_by_name(self, name: str) -> Dict:
        """根据姓名获取用户信息"""
        response = self.client.get(f"/sysuser/byName", params={"name": name})
        return response.json()
    
    def list_users(self, page: int = 1, size: int = 10) -> Dict:
        """获取用户列表"""
        response = self.client.get(f"/sysuser/list", params={"page": page, "size": size})
        return response.json()
    
    def search_users(self, keyword: str) -> List[Dict]:
        """搜索用户"""
        response = self.client.get(f"/sysuser/search", params={"keyword": keyword})
        return response.json()
    
    def get_user_details(self, user_id: int) -> Dict:
        """获取用户详细信息"""
        response = self.client.get(f"/sysuser/{user_id}")
        return response.json()