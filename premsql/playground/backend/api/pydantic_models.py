from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from premsql.agents.models import AgentOutput
from premsql.security import normalize_base_url, validate_session_name

# All the Session Models


class SessionCreationRequest(BaseModel):
    base_url: str = Field(...)
    model_config = ConfigDict(extra="forbid")

    @field_validator("base_url")
    @classmethod
    def validate_base_url(cls, value: str) -> str:
        return normalize_base_url(value)


class SessionCreationResponse(BaseModel):
    status_code: Literal[200, 401, 500] = Field(...)
    status: Literal["success", "error"] = Field(...)

    session_id: Optional[int] = None
    session_name: Optional[str] = None
    # db_connection_uri and session_db_path removed - sensitive, never exposed
    created_at: Optional[datetime] = None
    error_message: Optional[str] = None


class SessionSummary(BaseModel):
    session_id: int
    session_name: str
    created_at: datetime
    base_url: str
    # db_connection_uri and session_db_path removed - sensitive, never exposed

    model_config = ConfigDict(from_attributes=True)


class SessionListResponse(BaseModel):
    status_code: Literal[200, 401, 404, 500]
    status: Literal["success", "error"]
    sessions: Optional[List[SessionSummary]] = None
    total_count: Optional[int] = None
    page: Optional[int] = None
    page_size: Optional[int] = None
    error_message: Optional[str] = None


class SessionDeleteResponse(BaseModel):
    session_name: str
    status_code: Literal[200, 401, 404, 500]
    status: Literal["success", "error"]
    error_message: Optional[str] = None


# All the chat message models


class CompletionCreationRequest(BaseModel):
    session_name: str = Field(..., min_length=1, max_length=64)
    question: str = Field(..., min_length=1, max_length=4000)

    @field_validator("session_name")
    @classmethod
    def validate_session_name_value(cls, value: str) -> str:
        return validate_session_name(value)


class CompletionCreationResponse(BaseModel):
    status_code: Literal[200, 401, 404, 500]
    status: Literal["success", "error"]
    message_id: Optional[int] = None
    session_name: Optional[str] = None
    created_at: Optional[datetime] = None
    message: Optional[AgentOutput] = None
    question: Optional[str] = None
    error_message: Optional[str] = None


class CompletionSummary(BaseModel):
    message_id: int
    session_name: str
    # base_url removed - not needed in chat history
    created_at: datetime
    question: Optional[str] = None
    message: Optional[AgentOutput] = None

    model_config = ConfigDict(from_attributes=True)


class CompletionListResponse(BaseModel):
    status_code: Literal[200, 401, 404, 500]
    status: Literal["success", "error"]
    completions: Optional[List[CompletionSummary]] = None
    total_count: Optional[int] = None
    page: Optional[int] = None
    page_size: Optional[int] = None
    error_message: Optional[str] = None
