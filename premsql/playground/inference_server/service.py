from contextlib import asynccontextmanager
from datetime import datetime
import os
from typing import Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from premsql.logger import setup_console_logger
from premsql.agents.base import AgentBase, AgentOutput
from premsql.security import (
    PREMSQL_API_TOKEN_HEADER,
    PremSQLException,
    get_allowed_origins,
    get_api_token,
    redact_agent_output_payload,
    safe_error_message,
)

logger = setup_console_logger("[FASTAPI-INFERENCE-SERVICE]")

# Check if in debug mode
DJANGO_DEBUG = os.environ.get("PREMSQL_DJANGO_DEBUG", "false").lower() == "true"


class QuestionInput(BaseModel):
    question: str = Field(..., min_length=1, max_length=4000)


class SessionInfoResponse(BaseModel):
    status: int
    session_name: Optional[str] = None
    db_connection_uri: Optional[str] = None
    session_db_path: Optional[str] = None
    base_url: Optional[str] = None
    created_at: Optional[datetime] = None


class ChatHistoryResponse(BaseModel):
    message_id: int
    agent_output: AgentOutput


class CompletionResponse(BaseModel):
    message_id: int
    message: AgentOutput


class AgentServer:
    def __init__(
        self,
        agent: AgentBase,
        url: Optional[str] = "localhost",
        port: Optional[int] = 8100,
        api_token: Optional[str] = None,
    ) -> None:
        self.agent = agent
        self.port = port
        self.url = url
        # Always get a token (either from config or auto-generated dev token)
        self.api_token = get_api_token(api_token)
        # Track if this is an auto-generated dev token
        self._is_dev_token = api_token is None and not self._check_env_token()
        self.app = self.create_app()

    def _check_env_token(self) -> bool:
        """Check if token was set in environment"""
        import os
        return os.environ.get("PREMSQL_API_TOKEN") is not None

    def _authorize_request(self, request: Request) -> None:
        # In debug mode, skip authentication
        if DJANGO_DEBUG:
            return
        if not self.api_token:
            return
        if request.headers.get(PREMSQL_API_TOKEN_HEADER) != self.api_token:
            raise HTTPException(status_code=401, detail="Unauthorized")

    @asynccontextmanager
    async def lifespan(self, app: FastAPI):
        # Startup: Log the initialization
        logger.info("Starting up the application")
        yield
        # Shutdown: Clean up resources
        logger.info("Shutting down the application")
        if hasattr(self.agent, "cleanup"):
            await self.agent.cleanup()

    def create_app(self):
        app = FastAPI(lifespan=self.lifespan)
        app.add_middleware(
            CORSMiddleware,
            allow_origins=get_allowed_origins(),
            allow_credentials=False,
            allow_methods=["GET", "POST", "DELETE"],
            allow_headers=["Content-Type", PREMSQL_API_TOKEN_HEADER],
        )

        @app.post("/completion", response_model=CompletionResponse)
        async def completion(input_data: QuestionInput, request: Request):
            self._authorize_request(request)
            try:
                result = self.agent(question=input_data.question, server_mode=True)
                message_id = self.agent.history.get_latest_message_id()
                payload = redact_agent_output_payload(result.model_dump())
                return CompletionResponse(
                    message=AgentOutput(**payload), message_id=message_id
                )
            except Exception as exc:
                # Use safe error message for logging (whitelist approach)
                logger.error(safe_error_message(exc, debug_mode=False))
                # Return safe message to user
                raise HTTPException(
                    status_code=500,
                    detail=safe_error_message(exc, debug_mode=False)
                )

        # TODO: I need a method which will just get the "latets message_id"

        @app.get("/chat_history/{message_id}", response_model=ChatHistoryResponse)
        async def get_chat_history(message_id: int, request: Request):
            self._authorize_request(request)
            try:
                exit_output = self.agent.history.get_by_message_id(
                    message_id=message_id
                )
                if exit_output is None:
                    raise HTTPException(
                        status_code=404,
                        detail=f"Message with ID {message_id} not found",
                    )
                agent_output = self.agent.convert_exit_output_to_agent_output(
                    exit_output=exit_output
                )
                payload = redact_agent_output_payload(agent_output.model_dump())
                return ChatHistoryResponse(
                    message_id=message_id, agent_output=AgentOutput(**payload)
                )
            except Exception as exc:
                logger.error(safe_error_message(exc, debug_mode=False))
                raise HTTPException(
                    status_code=500,
                    detail=safe_error_message(exc, debug_mode=False)
                )

        @app.get("/")
        async def health_check(request: Request):
            self._authorize_request(request)
            return {
                "status_code": 200, 
                "status": f"healthy, running: {self.agent.session_name}"
            }

        @app.get("/health")
        async def health_check_no_auth(request: Request):
            # Health check doesn't require authentication
            return {"status_code": 200, "status": "healthy"}

        @app.get("/session_info", response_model=SessionInfoResponse)
        async def get_session_info(request: Request):
            self._authorize_request(request)
            try:
                session_name = getattr(self.agent, "session_name", None)
                if session_name is None:
                    raise ValueError("Session name is not available")

                return SessionInfoResponse(
                    status=200,
                    session_name=session_name,
                    db_connection_uri=None,
                    session_db_path=None,
                    base_url=f"http://{self.url}:{self.port}",
                    created_at=datetime.now(),
                )
            except Exception as exc:
                logger.error(safe_error_message(exc, debug_mode=False))
                return SessionInfoResponse(
                    status=500,
                    session_name=None,
                    db_connection_uri=None,
                    session_db_path=None,
                    base_url=None,
                    created_at=None,
                )

        @app.delete("/session")
        async def delete_session(request: Request):
            self._authorize_request(request)
            try:
                self.agent.history.delete_table()
                # Recreate the table for future queries
                self.agent.history.create_table_if_not_exists()
                return {"status_code": 200, "status": "success"}
            except Exception as exc:
                logger.error(safe_error_message(exc, debug_mode=False))
                raise HTTPException(
                    status_code=500,
                    detail=safe_error_message(exc, debug_mode=False)
                )

        return app

    def launch(self):
        import uvicorn

        logger.info(f"Starting server on port {self.port}")
        if self._is_dev_token:
            logger.info(f"Using auto-generated dev token: {self.api_token}")
        else:
            logger.info(f"Using configured API token")
        uvicorn.run(self.app, host=self.url, port=int(self.port))
