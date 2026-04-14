import os
from typing import Optional

from premsql.logger import setup_console_logger
from premsql.security import PREMSQL_API_TOKEN_HEADER, get_api_token

logger = setup_console_logger("[BACKEND-UTILS]")

# Check if in debug mode
DJANGO_DEBUG = os.environ.get("PREMSQL_DJANGO_DEBUG", "false").lower() == "true"


def is_request_authorized(headers: dict, explicit_token: Optional[str] = None) -> bool:
    # In debug mode, skip authentication
    if DJANGO_DEBUG:
        return True

    required_token = get_api_token(explicit_token)
    if not required_token:
        return True
    return headers.get(PREMSQL_API_TOKEN_HEADER) == required_token


def clamp_pagination(page: int, page_size: int, max_page_size: int = 100) -> tuple[int, int]:
    if page < 1:
        page = 1
    if page_size < 1:
        page_size = 1
    if page_size > max_page_size:
        page_size = max_page_size
    return page, page_size
