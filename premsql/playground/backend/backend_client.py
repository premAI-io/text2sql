import requests

from premsql.logger import setup_console_logger
from premsql.playground.backend.api.pydantic_models import (
    CompletionCreationRequest,
    CompletionCreationResponse,
    CompletionListResponse,
    SessionCreationRequest,
    SessionCreationResponse,
    SessionDeleteResponse,
    SessionListResponse,
)
from premsql.security import build_auth_headers

BASE_URL = "http://127.0.0.1:8000/api"

logger = setup_console_logger("BACKEND-API-CLIENT")


class BackendAPIClient:
    def __init__(self, api_token: str | None = None, timeout: int = 180):
        self.base_url = BASE_URL
        self.timeout = timeout
        self.headers = build_auth_headers(
            {
                "accept": "application/json",
                "Content-Type": "application/json",
            },
            token=api_token,
        )

    def create_session(self, request: SessionCreationRequest) -> SessionCreationResponse:
        try:
            response = requests.post(
                f"{self.base_url}/session/create",
                json=request.model_dump(),
                headers=self.headers,
                timeout=self.timeout,
            )
            response.raise_for_status()
            return SessionCreationResponse(**response.json())
        except requests.RequestException as exc:
            logger.error(f"Error creating session: {exc}")
            return SessionCreationResponse(
                status="error",
                status_code=(
                    response.status_code
                    if "response" in locals() and hasattr(response, "status_code")
                    else 500
                ),
                error_message="Failed to create session",
            )
        except ValueError as exc:
            logger.error(f"Error parsing session creation response: {exc}")
            return SessionCreationResponse(
                status="error",
                status_code=500,
                error_message="Failed to parse server response",
            )

    def list_sessions(self, page: int = 1, page_size: int = 20) -> SessionListResponse:
        try:
            response = requests.get(
                f"{self.base_url}/session/list/",
                params={"page": page, "page_size": page_size},
                headers=self.headers,
                timeout=self.timeout,
            )
            response.raise_for_status()
            return SessionListResponse(**response.json())
        except requests.RequestException as exc:
            logger.error(f"Error listing sessions: {exc}")
            return SessionListResponse(
                status="error",
                status_code=(
                    response.status_code
                    if "response" in locals() and hasattr(response, "status_code")
                    else 500
                ),
                error_message="Failed to list sessions",
                sessions=[],
                total_count=0,
                page=page,
                page_size=page_size,
            )
        except ValueError as exc:
            logger.error(f"Error parsing session list response: {exc}")
            return SessionListResponse(
                status="error",
                status_code=500,
                error_message="Failed to parse server response",
                sessions=[],
                total_count=0,
                page=page,
                page_size=page_size,
            )

    def get_session(self, session_name: str) -> SessionListResponse:
        try:
            response = requests.get(
                f"{self.base_url}/session/{session_name}/",
                headers=self.headers,
                timeout=self.timeout,
            )
            response.raise_for_status()
            return SessionListResponse(**response.json())
        except requests.RequestException as exc:
            logger.error(f"Error getting session: {exc}")
            status_code = (
                response.status_code
                if "response" in locals() and hasattr(response, "status_code")
                else 500
            )
            return SessionListResponse(
                status="error",
                status_code=status_code,
                error_message="Failed to get session",
                sessions=[],
                total_count=0,
                page=1,
                page_size=1,
            )
        except ValueError as exc:
            logger.error(f"Error parsing session response: {exc}")
            return SessionListResponse(
                status="error",
                status_code=500,
                error_message="Failed to parse server response",
                sessions=[],
                total_count=0,
                page=1,
                page_size=1,
            )

    def delete_session(self, session_name: str) -> SessionDeleteResponse:
        try:
            response = requests.delete(
                f"{self.base_url}/session/{session_name}",
                headers=self.headers,
                timeout=self.timeout,
            )
            response.raise_for_status()
            return SessionDeleteResponse(**response.json())
        except requests.RequestException as exc:
            logger.error(f"Error deleting session: {exc}")
            return SessionDeleteResponse(
                session_name=session_name,
                status="error",
                status_code=(
                    response.status_code
                    if "response" in locals() and hasattr(response, "status_code")
                    else 500
                ),
                error_message="Failed to delete session",
            )
        except ValueError as exc:
            logger.error(f"Error parsing session deletion response: {exc}")
            return SessionDeleteResponse(
                session_name=session_name,
                status="error",
                status_code=500,
                error_message="Failed to parse server response",
            )

    def create_completion(
        self, request: CompletionCreationRequest
    ) -> CompletionCreationResponse:
        try:
            response = requests.post(
                f"{self.base_url}/chat/completion",
                json=request.model_dump(),
                headers=self.headers,
                timeout=self.timeout,
            )
            response.raise_for_status()
            return CompletionCreationResponse(**response.json())
        except requests.RequestException as exc:
            logger.error(f"Error creating completion: {exc}")
            return CompletionCreationResponse(
                status="error",
                status_code=(
                    response.status_code
                    if "response" in locals() and hasattr(response, "status_code")
                    else 500
                ),
                error_message="Failed to create completion",
            )
        except ValueError as exc:
            logger.error(f"Error parsing completion response: {exc}")
            return CompletionCreationResponse(
                status="error",
                status_code=500,
                error_message="Failed to parse server response",
            )

    def get_chat_history(
        self, session_name: str, page: int = 1, page_size: int = 20
    ) -> CompletionListResponse:
        try:
            response = requests.get(
                f"{self.base_url}/chat/history/{session_name}/",
                params={"page": page, "page_size": page_size},
                headers=self.headers,
                timeout=self.timeout,
            )
            response.raise_for_status()
            return CompletionListResponse(**response.json())
        except requests.RequestException as exc:
            logger.error(f"Error getting chat history: {exc}")
            return CompletionListResponse(
                status="error",
                status_code=(
                    response.status_code
                    if "response" in locals() and hasattr(response, "status_code")
                    else 500
                ),
                error_message="Failed to get chat history",
                completions=[],
                total_count=0,
                page=page,
                page_size=page_size,
            )
        except ValueError as exc:
            logger.error(f"Error parsing chat history response: {exc}")
            return CompletionListResponse(
                status="error",
                status_code=500,
                error_message="Failed to parse server response",
                completions=[],
                total_count=0,
                page=page,
                page_size=page_size,
            )
