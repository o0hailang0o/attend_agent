import logging
import httpx
from typing import Dict, Any, Optional
from app.core.config import settings
from app.context import auth_token

logger = logging.getLogger(__name__)


def _to_dict(response: httpx.Response) -> Dict:
    """安全地将 httpx 响应转为 dict，非 dict/null 时返回空 dict"""
    try:
        data = response.json()
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _log_request(request: httpx.Request):
    token_header = request.headers.get("Authorization", "")
    logger.info(">>> %s %s, Authorization=%s",
                request.method, request.url, "已设置" if token_header else "空")


def _log_response(response: httpx.Response):
    logger.info("<<< %s %s, status=%s",
                response.request.method, response.request.url, response.status_code)


def get_client(base_url: str = None) -> httpx.Client:
    """创建带认证 token 的 httpx 客户端"""
    url = base_url or settings.attend_base_url or "http://localhost:8080"
    token = auth_token.get()
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    client = httpx.Client(base_url=url, headers=headers)
    client.event_hooks = {"request": [_log_request], "response": [_log_response]}
    return client


class AttendApiClient:
    def __init__(self):
        self.base_url = settings.attend_base_url or "http://localhost:8080"
        self.client = get_client(self.base_url)
    
    def get(self, endpoint: str, params: Optional[Dict] = None) -> Dict:
        """GET请求"""
        response = self.client.get(endpoint, params=params)
        response.raise_for_status()
        return response.json()
    
    def post(self, endpoint: str, data: Optional[Dict] = None) -> Dict:
        """POST请求"""
        response = self.client.post(endpoint, json=data)
        response.raise_for_status()
        return response.json()
    
    def put(self, endpoint: str, data: Optional[Dict] = None) -> Dict:
        """PUT请求"""
        response = self.client.put(endpoint, json=data)
        response.raise_for_status()
        return response.json()
    
    def delete(self, endpoint: str) -> Dict:
        """DELETE请求"""
        response = self.client.delete(endpoint)
        response.raise_for_status()
        return response.json()