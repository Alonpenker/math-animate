from dataclasses import dataclass
from typing import Optional, Tuple, Type, Union

from fastapi import HTTPException, Request, status
from fastapi.exception_handlers import (
    http_exception_handler,
    request_validation_exception_handler,
)
from fastapi.exceptions import RequestValidationError
from celery.exceptions import OperationalError
from kombu.exceptions import SerializationError
from minio.error import S3Error
from psycopg2 import Error as PsycopgError

from app.exceptions.invalid_transition_error import InvalidTransitionError
from app.utils.logging import get_logger

ExcType = Union[Type[Exception], Tuple[Type[Exception], ...]]

@dataclass(frozen=True)
class ErrorSpec:
    exc: ExcType
    status_code: int
    detail: Optional[str]


ERROR_SPECS: tuple[ErrorSpec, ...] = (
    ErrorSpec(InvalidTransitionError, status.HTTP_409_CONFLICT, None),
    ErrorSpec(OperationalError, status.HTTP_503_SERVICE_UNAVAILABLE, "Task queue unavailable."),
    ErrorSpec(PsycopgError, status.HTTP_503_SERVICE_UNAVAILABLE, "Postgres Database unavailable."),
    ErrorSpec(SerializationError, status.HTTP_500_INTERNAL_SERVER_ERROR, "Task payload serialization failed."),
    ErrorSpec(S3Error, status.HTTP_502_BAD_GATEWAY, "Failed to access S3."),
    ErrorSpec((KeyError, ValueError), status.HTTP_400_BAD_REQUEST, None),
    ErrorSpec(RuntimeError, status.HTTP_500_INTERNAL_SERVER_ERROR, None),
)

logger = get_logger(__name__)


def _match_error(exc: Exception) -> Optional[HTTPException]:
    for spec in ERROR_SPECS:
        if isinstance(exc, spec.exc):
            detail = spec.detail if spec.detail else str(exc)
            return HTTPException(status_code=spec.status_code, detail=detail)
    return None


async def handle_exceptions(request: Request, exc: Exception):
    if isinstance(exc, HTTPException):
        return await http_exception_handler(request, exc)

    if isinstance(exc, RequestValidationError):
        return await request_validation_exception_handler(request, exc)

    logger.exception("Unhandled exception", exc_info=exc)

    mapped = _match_error(exc)
    if mapped is not None:
        return await http_exception_handler(request, mapped)

    return await http_exception_handler(
        request,
        HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error",
        ),
    )
