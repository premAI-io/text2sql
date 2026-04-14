import ast
import json
import logging
import os
import re
import secrets
from pathlib import Path
from typing import Any, Iterable, Optional
from urllib.parse import urlparse

try:
    import sqlparse
except ImportError:  # pragma: no cover - fallback exercised in minimal envs
    sqlparse = None

SESSION_NAME_PATTERN = re.compile(r"^[A-Za-z0-9_-]{1,64}$")
SAFE_FILENAME_PATTERN = re.compile(r"[^A-Za-z0-9._-]+")
FORBIDDEN_SQL_PATTERN = re.compile(
    r"\b("
    r"INSERT|UPDATE|DELETE|DROP|ALTER|ATTACH|DETACH|PRAGMA|REPLACE|"
    r"CREATE|TRUNCATE|MERGE|GRANT|REVOKE|VACUUM|ANALYZE|COPY|CALL"
    r")\b",
    re.IGNORECASE,
)
CODE_FENCE_PATTERN = re.compile(r"^```(?:json|python)?\s*(.*?)\s*```$", re.DOTALL)
LOOPBACK_HOSTS = {"127.0.0.1", "localhost", "::1"}
DEFAULT_ALLOWED_ORIGINS = (
    "http://127.0.0.1:8501",
    "http://localhost:8501",
)
PREMSQL_API_TOKEN_HEADER = "X-PremSQL-API-Token"
PREMSQL_API_TOKEN_ENV = "PREMSQL_API_TOKEN"

# Auto-generated dev token (only used when PREMSQL_API_TOKEN not configured)
_DEV_API_TOKEN: Optional[str] = None


class SecurityValidationError(ValueError):
    """Base exception for security validation failures with safe messages."""
    def __init__(self, message: str, *args):
        # All security validation errors are safe to expose (they're validation messages)
        self.safe_message = message
        super().__init__(message, *args)


class UnsafeSQLQuery(SecurityValidationError):
    """Exception for unsafe SQL queries."""
    pass


class PremSQLException(Exception):
    """
    Custom exception base class that forces developers to explicitly declare safe messages.
    All PremSQL exceptions should inherit from this class for production use.
    """
    def __init__(self, safe_message: str, internal_message: Optional[str] = None, *args):
        self.safe_message = safe_message  # Safe message to expose to users/logs
        self.internal_message = internal_message or safe_message  # For internal debugging
        super().__init__(internal_message or safe_message, *args)


def safe_error_message(exc: Exception, debug_mode: bool = False) -> str:
    """
    Generate a safe error message for external exposure using pure whitelist approach.

    Security principle: Never try to filter/strip bad content (blacklist).
    Only expose what we explicitly know is safe (whitelist).

    Args:
        exc: The exception to generate message from
        debug_mode: If True, include more details (only for trusted environments)

    Returns:
        A safe message that doesn't expose sensitive information
    """
    # Whitelist approach: only expose what we explicitly allow

    # 1. PremSQLException and SecurityValidationError have explicitly declared safe messages
    if isinstance(exc, (PremSQLException, SecurityValidationError)):
        return exc.safe_message

    # 2. HTTPException from FastAPI - use the detail field which is designed for user display
    if hasattr(exc, 'detail') and isinstance(exc.detail, str):
        return exc.detail

    # 3. In debug mode (trusted environment only), allow more details
    if debug_mode:
        # Still only for known safe exception types
        if isinstance(exc, (ValueError, TypeError, KeyError)):
            msg = str(exc)
            return msg[:200] if len(msg) > 200 else msg

    # 4. For all other exceptions: DO NOT expose any message content
    # Only expose the exception type name - this is safe metadata
    return f"An error occurred ({type(exc).__name__}). Please try again or contact support."


def validate_session_name(session_name: str) -> str:
    if session_name is None:
        raise SecurityValidationError("Session name is required")

    normalized = session_name.strip()
    if not SESSION_NAME_PATTERN.fullmatch(normalized):
        raise SecurityValidationError(
            "Session name must contain only letters, numbers, underscores, or hyphens "
            "and be at most 64 characters long"
        )
    return normalized


def quote_sqlite_identifier(identifier: str) -> str:
    return f'"{validate_session_name(identifier)}"'


def sanitize_filename(filename: str) -> str:
    if filename is None:
        raise SecurityValidationError("Filename is required")

    basename = Path(filename).name.strip()
    if not basename or basename in {".", ".."}:
        raise SecurityValidationError("Filename is invalid")

    sanitized = SAFE_FILENAME_PATTERN.sub("_", basename)
    if not sanitized or sanitized in {".", ".."}:
        raise SecurityValidationError("Filename is invalid after sanitization")
    return sanitized


def resolve_path_within_root(root: Path | str, *parts: str) -> Path:
    root_path = Path(root).resolve()
    target = root_path.joinpath(*parts).resolve()
    if target != root_path and root_path not in target.parents:
        raise SecurityValidationError("Resolved path escapes the configured root")
    return target


def normalize_base_url(base_url: str) -> str:
    if not base_url:
        raise SecurityValidationError("Base URL is required")

    candidate = base_url.strip()
    if "://" not in candidate:
        candidate = f"http://{candidate}"

    parsed = urlparse(candidate)
    if parsed.scheme not in {"http", "https"}:
        raise SecurityValidationError("Base URL must use http or https")
    if parsed.hostname not in LOOPBACK_HOSTS:
        raise SecurityValidationError(
            "Base URL must point to a local loopback address"
        )
    if parsed.username or parsed.password:
        raise SecurityValidationError("Credentials are not allowed in base URLs")
    if parsed.path not in {"", "/"} or parsed.params or parsed.query or parsed.fragment:
        raise SecurityValidationError(
            "Base URL must only include scheme, host, and port"
        )
    if parsed.port is None:
        raise SecurityValidationError("Base URL must include an explicit port")

    host = parsed.hostname
    if ":" in host and not host.startswith("["):
        host = f"[{host}]"
    return f"{parsed.scheme}://{host}:{parsed.port}"


def strip_code_fences(content: str) -> str:
    if content is None:
        raise SecurityValidationError("Model output is empty")

    cleaned = content.strip()
    match = CODE_FENCE_PATTERN.match(cleaned)
    if match:
        return match.group(1).strip()
    return cleaned


def parse_structured_output(
    content: str, expected_keys: Optional[Iterable[str]] = None
) -> dict[str, Any]:
    cleaned = strip_code_fences(content)

    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError:
        pythonish = (
            cleaned.replace("null", "None")
            .replace("true", "True")
            .replace("false", "False")
        )
        try:
            parsed = ast.literal_eval(pythonish)
        except (ValueError, SyntaxError) as exc:
            raise SecurityValidationError(
                "Model output must be valid JSON"
            ) from exc

    if not isinstance(parsed, dict):
        raise SecurityValidationError("Structured model output must be a JSON object")

    if expected_keys is not None:
        expected = set(expected_keys)
        missing = expected - set(parsed)
        if missing:
            raise SecurityValidationError(
                f"Structured model output is missing keys: {', '.join(sorted(missing))}"
            )
    return parsed


def ensure_expected_keys_only(
    data: dict[str, Any], expected_keys: Iterable[str]
) -> dict[str, Any]:
    expected = set(expected_keys)
    unexpected = set(data) - expected
    if unexpected:
        raise SecurityValidationError(
            f"Structured model output contains unexpected keys: "
            f"{', '.join(sorted(unexpected))}"
        )
    return data


def normalize_sql(sql: str) -> str:
    if not sql or not sql.strip():
        raise UnsafeSQLQuery("SQL query is empty")

    if sqlparse is not None:
        cleaned = sqlparse.format(sql, strip_comments=True).strip()
        statements = [
            statement.strip() for statement in sqlparse.split(cleaned) if statement.strip()
        ]
    else:
        cleaned = re.sub(r"--.*?$", "", sql, flags=re.MULTILINE).strip()
        statements = [statement.strip() for statement in cleaned.split(";") if statement.strip()]
    if len(statements) != 1:
        raise UnsafeSQLQuery("Only a single SQL statement is allowed")
    return statements[0]


def enforce_read_only_sql(sql: str) -> str:
    normalized = normalize_sql(sql)
    upper_sql = normalized.upper()
    if not (upper_sql.startswith("SELECT") or upper_sql.startswith("WITH")):
        raise UnsafeSQLQuery("Only read-only SELECT queries are allowed")
    if FORBIDDEN_SQL_PATTERN.search(upper_sql):
        raise UnsafeSQLQuery("Potentially destructive SQL statements are not allowed")
    return normalized


def mask_db_connection_uri(db_connection_uri: Optional[str]) -> Optional[str]:
    if not db_connection_uri:
        return None

    if db_connection_uri.startswith("sqlite:///"):
        return "sqlite:///***"

    parsed = urlparse(db_connection_uri)
    if parsed.scheme:
        return f"{parsed.scheme}://***"
    return "***"


def redact_agent_output_payload(payload: Optional[dict[str, Any]]) -> Optional[dict[str, Any]]:
    if payload is None:
        return None

    sanitized = dict(payload)
    sanitized["db_connection_uri"] = None
    return sanitized


def get_api_token(explicit_token: Optional[str] = None) -> Optional[str]:
    """
    Get API token from explicit parameter, environment, or auto-generate for dev.

    For production (DEBUG=false): PREMSQL_API_TOKEN must be configured
    For development (DEBUG=true): Auto-generates a random token if not configured
    """
    token = explicit_token or os.environ.get(PREMSQL_API_TOKEN_ENV)
    if token:
        return token

    # Check if in debug mode
    debug_mode = os.environ.get("PREMSQL_DJANGO_DEBUG", "false").lower() == "true"

    if not debug_mode:
        # Production mode: Token must be configured
        raise ValueError(
            "PREMSQL_API_TOKEN must be configured for production. "
            "Set PREMSQL_API_TOKEN environment variable or set PREMSQL_DJANGO_DEBUG=true for development."
        )

    # Development mode: Auto-generate dev token
    global _DEV_API_TOKEN
    if _DEV_API_TOKEN is None:
        _DEV_API_TOKEN = f"dev-{secrets.token_hex(16)}"
        logging.getLogger("premsql.security").warning(
            f"Auto-generated dev API token: {_DEV_API_TOKEN} "
            "(Set PREMSQL_API_TOKEN for production)"
        )
    return _DEV_API_TOKEN


def build_auth_headers(
    headers: Optional[dict[str, str]] = None, token: Optional[str] = None
) -> dict[str, str]:
    merged = dict(headers or {})
    api_token = get_api_token(token)
    if api_token:
        merged[PREMSQL_API_TOKEN_HEADER] = api_token
    return merged


def get_allowed_origins() -> list[str]:
    configured = os.environ.get("PREMSQL_ALLOWED_ORIGINS")
    if not configured:
        return list(DEFAULT_ALLOWED_ORIGINS)
    return [origin.strip() for origin in configured.split(",") if origin.strip()]
