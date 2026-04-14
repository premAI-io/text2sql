from typing import Any, Dict, Optional
from urllib.parse import urljoin

import requests

from premsql.security import build_auth_headers


class InferenceServerAPIError(Exception):
    pass


class InferenceServerAPIClient:
    def __init__(self, timeout: int = 120, api_token: Optional[str] = None) -> None:
        self.headers = build_auth_headers(
            {
            "accept": "application/json",
            "Content-Type": "application/json",
            },
            token=api_token,
        )
        self.timeout = timeout

    def _make_request(
        self,
        base_url: str,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        url = urljoin(base_url.rstrip("/"), endpoint)
        try:
            response = requests.request(
                method, url, headers=self.headers, json=data, timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            raise InferenceServerAPIError(f"API request failed: {str(e)}")
    
    def is_online(self, base_url: str) -> bool:
        endpoint = "/health"
        try:
            response = self._make_request(base_url, "GET", endpoint)
            return response.get("status_code")
        except Exception as e:
            return 500

    def post_completion(self, base_url: str, question: str) -> Dict[str, Any]:
        if not question.strip():
            raise ValueError("Question cannot be empty")
        endpoint = "/completion"
        data = {"question": question}
        return self._make_request(base_url, "POST", endpoint, data)

    def get_session_info(self, base_url: str) -> Dict[str, Any]:
        endpoint = "/session_info"
        return self._make_request(base_url, "GET", endpoint)

    def get_chat_history(self, base_url: str, message_id: int) -> Dict[str, Any]:
        if message_id < 1:
            raise ValueError("Message ID must be a positive integer")
        endpoint = f"/chat_history/{message_id}"
        return self._make_request(base_url, "GET", endpoint)

    def delete_session(self, base_url: str) -> Dict[str, Any]:
        endpoint = "/session"
        return self._make_request(base_url, "DELETE", endpoint)
