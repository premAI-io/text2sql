import json

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from pydantic import ValidationError as PydanticValidationError
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from premsql.logger import setup_console_logger
from premsql.playground.backend.api.pydantic_models import (
    CompletionCreationRequest,
    SessionCreationRequest,
    SessionListResponse,
    SessionSummary,
)
from premsql.playground.backend.api.serializers import (
    CompletionCreationRequestSerializer,
    CompletionCreationResponseSerializer,
    CompletionListResponseSerializer,
    SessionCreationRequestSerializer,
    SessionCreationResponseSerializer,
    SessionListResponseSerializer,
    SessionSummarySerializer,
)

from .services import CompletionService, SessionManageService
from .utils import clamp_pagination, is_request_authorized

logger = setup_console_logger("[VIEWS]")


def _authorize_or_401(request):
    if is_request_authorized(request.headers):
        return None
    return Response(
        {"status": "error", "error_message": "Unauthorized"},
        status=status.HTTP_401_UNAUTHORIZED,
    )


@swagger_auto_schema(
    method="post",
    request_body=SessionCreationRequestSerializer,
    responses={
        200: SessionCreationResponseSerializer,
        400: "Bad Request",
        500: SessionCreationResponseSerializer,
    },
)
@api_view(["POST"])
def create_session(request):
    unauthorized = _authorize_or_401(request)
    if unauthorized is not None:
        return unauthorized
    try:
        session_request = SessionCreationRequest(**request.data)
        response = SessionManageService().create_session(request=session_request)
        return Response(response.model_dump(), status=response.status_code)
    except (json.JSONDecodeError, ValueError, PydanticValidationError):
        return Response(
            {"status": "error", "error_message": "Invalid request payload"},
            status=status.HTTP_400_BAD_REQUEST,
        )
    except Exception:
        logger.exception("Unexpected error while creating a session")
        return Response(
            {"status": "error", "error_message": "Unable to create session"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@swagger_auto_schema(
    method="get",
    manual_parameters=[
        openapi.Parameter(
            "session_name",
            openapi.IN_PATH,
            description="Name of the session",
            type=openapi.TYPE_STRING,
        ),
    ],
    responses={
        200: SessionSummarySerializer,
        400: "Bad Request",
        500: SessionSummarySerializer,
    },
)
@api_view(["GET"])
def get_session(request, session_name):
    unauthorized = _authorize_or_401(request)
    if unauthorized is not None:
        return unauthorized
    session = SessionManageService().get_session(session_name=session_name)
    if session:
        session_summary = SessionSummary(
            session_id=session.session_id,
            session_name=session.session_name,
            created_at=session.created_at,
            base_url=session.base_url,
        )
        response = SessionListResponse(
            status="success",
            status_code=200,
            sessions=[session_summary.model_dump()],
            total_count=1,
            page=1,
            page_size=1,
        )
    else:
        response = SessionListResponse(
            status="error",
            status_code=404,
            error_message="The requested session does not exist.",
        )
    return Response(
        response.model_dump(),
        status=status.HTTP_200_OK if session else status.HTTP_404_NOT_FOUND,
    )


@swagger_auto_schema(
    method="get",
    manual_parameters=[
        openapi.Parameter(
            "page",
            openapi.IN_QUERY,
            description="Page number",
            type=openapi.TYPE_INTEGER,
            default=1,
        ),
        openapi.Parameter(
            "page_size",
            openapi.IN_QUERY,
            description="Number of items per page",
            type=openapi.TYPE_INTEGER,
            default=20,
        ),
    ],
    responses={
        200: SessionListResponseSerializer,
        400: "Bad Request",
        500: SessionListResponseSerializer,
    },
)
@api_view(["GET"])
def list_sessions(request):
    unauthorized = _authorize_or_401(request)
    if unauthorized is not None:
        return unauthorized
    try:
        page = int(request.query_params.get("page", 1))
        page_size = int(request.query_params.get("page_size", 20))
        page, page_size = clamp_pagination(page=page, page_size=page_size)
    except ValueError:
        return Response(
            {"status": "error", "error_message": "Invalid page or page_size parameter"},
            status=status.HTTP_400_BAD_REQUEST,
        )
    response = SessionManageService().list_session(page=page, page_size=page_size)
    return Response(response.model_dump(), status=response.status_code)


@swagger_auto_schema(
    method="delete",
    manual_parameters=[
        openapi.Parameter(
            "session_name",
            openapi.IN_PATH,
            description="Name of the session to delete",
            type=openapi.TYPE_STRING,
            required=True,
        ),
    ],
    responses={
        200: openapi.Response(
            "Session deleted successfully",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "status": openapi.Schema(
                        type=openapi.TYPE_STRING, example="success"
                    ),
                    "message": openapi.Schema(type=openapi.TYPE_STRING),
                },
            ),
        ),
        404: "Not Found",
        500: "Internal Server Error",
    },
)
@api_view(["DELETE"])
def delete_session(request, session_name):
    unauthorized = _authorize_or_401(request)
    if unauthorized is not None:
        return unauthorized
    try:
        result = SessionManageService().delete_session(session_name=session_name)
        return Response(result.model_dump(), status=result.status_code)
    except Exception:
        logger.exception("Unexpected error while deleting session")
        return Response(
            {"status": "error", "error_message": "Unable to delete session"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


# Completion Views


@swagger_auto_schema(
    method="post",
    request_body=CompletionCreationRequestSerializer,
    responses={
        200: CompletionCreationResponseSerializer,
        400: "Bad Request",
        404: "Not Found",
        500: "Internal Server Error",
    },
)
@api_view(["POST"])
def create_completion(request):
    unauthorized = _authorize_or_401(request)
    if unauthorized is not None:
        return unauthorized
    try:
        completion_request = CompletionCreationRequest(**request.data)
        response = CompletionService().completion(request=completion_request)
        return Response(
            response.model_dump(),
            status=response.status_code,
        )
    except (ValidationError, PydanticValidationError, ValueError) as e:
        return Response(
            {"status": "error", "error_message": str(e)},
            status=status.HTTP_400_BAD_REQUEST,
        )
    except Exception:
        logger.exception("Unexpected error while creating completion")
        return Response(
            {"status": "error", "error_message": "Unable to create completion"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@swagger_auto_schema(
    method="get",
    manual_parameters=[
        openapi.Parameter(
            "session_name",
            openapi.IN_PATH,
            description="Name of the session",
            type=openapi.TYPE_STRING,
            required=True,
        ),
        openapi.Parameter(
            "page",
            openapi.IN_QUERY,
            description="Page number",
            type=openapi.TYPE_INTEGER,
            default=1,
        ),
        openapi.Parameter(
            "page_size",
            openapi.IN_QUERY,
            description="Number of items per page",
            type=openapi.TYPE_INTEGER,
            default=20,
        ),
    ],
    responses={
        200: CompletionListResponseSerializer,
        400: "Bad Request",
        404: "Not Found",
        500: "Internal Server Error",
    },
)
@api_view(["GET"])
def get_chat_history(request, session_name):
    unauthorized = _authorize_or_401(request)
    if unauthorized is not None:
        return unauthorized
    try:
        page = int(request.query_params.get("page", 1))
        page_size = int(request.query_params.get("page_size", 20))
        page, page_size = clamp_pagination(page=page, page_size=page_size)

        response = CompletionService().chat_history(
            session_name=session_name, page=page, page_size=page_size
        )

        return Response(
            response.model_dump(),
            status=response.status_code,
        )
    except ValueError:
        return Response(
            {"status": "error", "error_message": "Invalid page or page_size parameter"},
            status=status.HTTP_400_BAD_REQUEST,
        )
    except Exception:
        logger.exception("Unexpected error while fetching chat history")
        return Response(
            {"status": "error", "error_message": "Unable to fetch chat history"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
