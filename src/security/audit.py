import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import structlog

from config import get_settings

settings = get_settings()

# Ensure log directory exists
Path(settings.log_file).parent.mkdir(parents=True, exist_ok=True)

# Plain file handler writing JSON Lines
_file_handler = logging.FileHandler(settings.log_file)
_file_handler.setLevel(logging.DEBUG)

_stream_handler = logging.StreamHandler()
_stream_handler.setLevel(getattr(logging, settings.log_level.upper(), logging.INFO))

logging.basicConfig(
    level=logging.DEBUG,
    handlers=[_file_handler, _stream_handler],
)

structlog.configure(
    processors=[
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.JSONRenderer(),
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
)

_audit_log = structlog.get_logger("audit")


def new_request_id() -> str:
    return str(uuid.uuid4())


def log_request(
    *,
    request_id: str,
    username: str,
    endpoint: str,
    user_input: str,
    extra: dict[str, Any] | None = None,
) -> None:
    _audit_log.info(
        "request_received",
        request_id=request_id,
        username=username,
        endpoint=endpoint,
        user_input=user_input[:200],           # truncate for log safety
        timestamp=datetime.now(timezone.utc).isoformat(),
        **(extra or {}),
    )


def log_response(
    *,
    request_id: str,
    username: str,
    status: str,
    output_preview: str,
    latency_ms: float,
    extra: dict[str, Any] | None = None,
) -> None:
    _audit_log.info(
        "request_completed",
        request_id=request_id,
        username=username,
        status=status,
        output_preview=output_preview[:200],
        latency_ms=round(latency_ms, 2),
        timestamp=datetime.now(timezone.utc).isoformat(),
        **(extra or {}),
    )


def log_security_event(
    *,
    request_id: str,
    username: str,
    event_type: str,
    detail: str,
) -> None:
    _audit_log.warning(
        "security_event",
        request_id=request_id,
        username=username,
        event_type=event_type,
        detail=detail,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )



def log_error(
    *,
    request_id: str,
    username: str,
    error: str,
    exc_info: bool = False,
) -> None:
    _audit_log.error(
        "request_error",
        request_id=request_id,
        username=username,
        error=error,
        timestamp=datetime.now(timezone.utc).isoformat(),
        exc_info=exc_info,
    )