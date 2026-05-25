import httpx
from typing import Dict, Any, Optional
from app.core.config import settings

class LeaveBalanceController:
    def __init__(self):
        self.base_url = settings.attend_base_url or "http://localhost:8080"
        self.client = httpx.Client(base_url=self.base_url)
    
    def get_leave_balance_by_account(self, account: str) -> Dict:
        """根据工号获取假期余额"""
        response = self.client.get("/leaveBalance/byAccount", params={"account": account})
        return response.json()
    
    def get_leave_balance_by_work_num(self, work_num: str) -> Dict:
        """根据工号获取假期余额"""
        response = self.client.get("/leaveBalance/byWorkNum", params={"work_num": work_num})
        return response.json()