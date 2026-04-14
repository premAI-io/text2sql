from typing import Optional

from api.models import Completions, Session
from api.pydantic_models import (
    CompletionCreationRequest,
    CompletionCreationResponse,
    CompletionListResponse,
    CompletionSummary,
    SessionCreationRequest,
    SessionCreationResponse,
    SessionDeleteResponse,
    SessionListResponse,
    SessionSummary,
)
from django.core.exceptions import ObjectDoesNotExist
from django.core.paginator import Paginator
from django.db import transaction

from premsql.logger import setup_console_logger
from premsql.agents.base import AgentOutput
from premsql.playground import InferenceServerAPIClient
from premsql.security import (
    SecurityValidationError,
    get_api_token,
    mask_db_connection_uri,
    redact_agent_output_payload,
    safe_error_message,
    validate_session_name,
)

logger = setup_console_logger("[SESSION-MANAGER]")

# TODO: # When delete a session, then it should delete the memory of the session
# TODO: # when fetching the history it should just give out the message_id in the current django db
# and then using that we can iteratively request the history to give history chats one by one


class SessionManageService:
    def __init__(self) -> None:
        self.client = InferenceServerAPIClient(api_token=get_api_token())

    def create_session(
        self, request: SessionCreationRequest
    ) -> SessionCreationResponse:
        try:
            response = self.client.get_session_info(base_url=request.base_url)
        except Exception as exc:
            logger.error(safe_error_message(exc, debug_mode=False))
            return SessionCreationResponse(
                status_code=500,
                status="error",
                error_message="Unable to contact the inference server",
            )

        if response.get("status") == 500:
            return SessionCreationResponse(
                status_code=500,
                status="error",
                error_message="Unable to start the session",
            )

        try:
            session_name = validate_session_name(response["session_name"])
            # If session with same name exists, delete it first
            existing_session = Session.objects.filter(session_name=session_name).first()
            if existing_session:
                Completions.objects.filter(session_name=session_name).delete()
                existing_session.delete()
                logger.info(f"Deleted existing session: {session_name}")

            session = Session.objects.create(
                session_name=session_name,
                db_connection_uri=mask_db_connection_uri(response.get("db_connection_uri"))
                or "***",
                base_url=request.base_url,
                session_db_path="",
            )
            logger.info(f"Successfully created session: {session_name}")
            return SessionCreationResponse(
                status_code=200,
                status="success",
                session_id=session.session_id,
                session_name=session.session_name,
                created_at=session.created_at,
                error_message=None,
            )
        except SecurityValidationError:
            return SessionCreationResponse(
                status_code=500,
                status="error",
                error_message="Inference server returned an invalid session identifier",
            )
        except Exception as exc:
            logger.error(safe_error_message(exc, debug_mode=False))
            return SessionCreationResponse(
                status_code=500,
                status="error",
                error_message="Unable to create the session",
            )

    def get_session(self, session_name: str) -> Optional[Session]:
        try:
            return Session.objects.get(session_name=session_name)
        except ObjectDoesNotExist:
            return None

    def list_session(self, page: int, page_size: int = 20) -> SessionListResponse:
        try:
            sessions = Session.objects.all().order_by("-created_at")
            paginator = Paginator(sessions, page_size)
            page_obj = paginator.get_page(page)
            session_summaries = [
                SessionSummary(
                    session_id=session.session_id,
                    session_name=session.session_name,
                    created_at=session.created_at,
                    base_url=session.base_url,
                )
                for session in page_obj
            ]
            return SessionListResponse(
                status="success",
                status_code=200,
                sessions=session_summaries,
                total_count=paginator.count,
                page=page,
                page_size=page_size,
            )
        except Exception as exc:
            logger.error(safe_error_message(exc, debug_mode=False))
            return SessionListResponse(
                status="error",
                status_code=500,
                sessions=None,
                total_count=0,
                page=page,
                page_size=page_size,
                error_message="Unable to list sessions",
            )

    def delete_session(self, session_name: str):
        try:
            with transaction.atomic():
                session = Session.objects.get(session_name=session_name)
                try:
                    self.client.delete_session(base_url=session.base_url)
                except Exception:
                    logger.warning("Unable to notify inference server during session deletion")

                Completions.objects.filter(session_name=session_name).delete()
                session.delete()
                logger.info("Deleted all the chats")
                return SessionDeleteResponse(
                    session_name=session_name,
                    status_code=200,
                    status="success",
                    error_message=None,
                )
        except Session.DoesNotExist:
            return SessionDeleteResponse(
                session_name=session_name,
                status_code=404,
                status="error",
                error_message="Session does not exist",
            )
        except Exception as exc:
            logger.error(safe_error_message(exc, debug_mode=False))
            return SessionDeleteResponse(
                session_name=session_name,
                status_code=500,
                status="error",
                error_message="Unable to delete the session",
            )


class CompletionService:
    def __init__(self) -> None:
        self.client = InferenceServerAPIClient(api_token=get_api_token())

    def completion(
        self, request: CompletionCreationRequest
    ) -> CompletionCreationResponse:
        try:
            session = Session.objects.get(session_name=request.session_name)
        except ObjectDoesNotExist:
            return CompletionCreationResponse(
                status_code=404,
                status="error",
                session_name=request.session_name,
                error_message=f"Session '{request.session_name}' not found",
            )

        try:
            session_inference_response = self.client.post_completion(
                base_url=session.base_url, question=request.question
            )
        except Exception as exc:
            logger.error(safe_error_message(exc, debug_mode=False))
            return CompletionCreationResponse(
                status_code=500,
                status="error",
                session_name=session.session_name,
                error_message="Unable to process the completion request",
            )

        try:
            message_payload = redact_agent_output_payload(
                session_inference_response.get("message")
            )
            if message_payload is None:
                raise ValueError("Completion response did not include a message payload")

            agent_output = AgentOutput(**message_payload)
            chat = Completions.objects.create(
                session=session,
                session_name=session.session_name,
                question=request.question,
                message_id=session_inference_response.get("message_id"),
                created_at=agent_output.created_at,
                agent_output=message_payload,
            )

            logger.info(
                f"Chat completion created successfully for session: {session.session_name}"
            )
            return CompletionCreationResponse(
                status_code=200,
                status="success",
                message_id=chat.message_id,
                session_name=session.session_name,
                created_at=chat.created_at,
                question=chat.question,
                message=agent_output,
            )

        except Exception as exc:
            logger.error(safe_error_message(exc, debug_mode=False))
            return CompletionCreationResponse(
                status_code=500,
                status="error",
                session_name=session.session_name,
                error_message="Completion succeeded but could not be stored",
            )

    def chat_history(
        self, session_name: str, page: int, page_size: int = 20
    ) -> CompletionListResponse:
        try:
            session = Session.objects.get(session_name=session_name)
        except ObjectDoesNotExist:
            return CompletionListResponse(
                status="error",
                status_code=404,
                completions=[],
                total_count=0,
                page=page,
                page_size=page_size,
                error_message=f"Session '{session_name}' not found",
            )

        try:
            completions = Completions.objects.filter(session=session).order_by(
                "created_at"
            )
            paginator = Paginator(completions, page_size)
            page_obj = paginator.get_page(page)

            completion_summaries = [
                CompletionSummary(
                    message_id=completion.message_id,
                    session_name=completion.session_name,
                    created_at=completion.created_at,
                    question=completion.question,
                    message=(
                        AgentOutput(**completion.agent_output)
                        if completion.agent_output is not None
                        else None
                    ),
                )
                for completion in page_obj
            ]

            return CompletionListResponse(
                status="success",
                status_code=200,
                completions=completion_summaries,
                total_count=completions.count(),
                page=page,
                page_size=page_size,
            )
        except Exception as exc:
            logger.error(safe_error_message(exc, debug_mode=False))
            return CompletionListResponse(
                status="error",
                status_code=500,
                completions=[],
                total_count=0,
                page=page,
                page_size=page_size,
                error_message="Unable to fetch chat history",
            )
