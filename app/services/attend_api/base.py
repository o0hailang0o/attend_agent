import httpx
from typing import Dict, Any, Optional
from app.core.config import settings

class AttendApiClient:
    def __init__(self):
        self.base_url = settings.attend_base_url or "http://localhost:8080"
        self.client = httpx.Client(base_url=self.base_url)
    
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