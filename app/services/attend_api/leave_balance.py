from typing import Dict, Any, Optional
from .base import get_client, _to_dict

import logging

logger = logging.getLogger(__name__)


class LeaveBalanceController:
    def __init__(self):
        self.client = get_client()
    
    def get_leave_balance_by_userUuid(self, userUuid: str) -> Dict:
        """根据工号获取假期余额"""
        logger.info("请求 /leaveBalance/byUser?userUuid=%s", userUuid)
        response = self.client.get("/leaveBalance/byUser", params={"userUuid": userUuid})
        logger.info("响应 status=%s, body=%s", response.status_code, response.text[:500])
        return _to_dict(response)
    
