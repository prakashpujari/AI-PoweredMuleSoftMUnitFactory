"""Centralized exception hierarchy and FastAPI exception handlers."""
from typing import Any, Optional

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from app.utils.logging import get_logger

logger = get_logger(__name__)


class MUnitFactoryError(Exception):
    """Base exception for all platform errors."""
    status_code: int = 500
    error_code: str = "INTERNAL_ERROR"

    def __init__(self, message: str, details: Optional[Any] = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details


class ApplicationNotFoundError(MUnitFactoryError):
    status_code = 404
    error_code = "APPLICATION_NOT_FOUND"


class FlowNotFoundError(MUnitFactoryError):
    status_code = 404
    error_code = "FLOW_NOT_FOUND"


class ParseError(MUnitFactoryError):
    status_code = 422
    error_code = "PARSE_ERROR"


class TestGenerationError(MUnitFactoryError):
    status_code = 500
    error_code = "TEST_GENERATION_FAILED"


class ExecutionError(MUnitFactoryError):
    status_code = 500
    error_code = "EXECUTION_FAILED"


class AIProviderError(MUnitFactoryError):
    status_code = 503
    error_code = "AI_PROVIDER_UNAVAILABLE"


class AuthenticationError(MUnitFactoryError):
    status_code = 401
    error_code = "AUTHENTICATION_FAILED"


class AuthorizationError(MUnitFactoryError):
    status_code = 403
    error_code = "AUTHORIZATION_FAILED"


class ValidationError(MUnitFactoryError):
    status_code = 422
    error_code = "VALIDATION_ERROR"


class RateLimitError(MUnitFactoryError):
    status_code = 429
    error_code = "RATE_LIMIT_EXCEEDED"


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(MUnitFactoryError)
    async def munit_exception_handler(request: Request, exc: MUnitFactoryError) -> JSONResponse:
        logger.error(
            "platform_error",
            error_code=exc.error_code,
            message=exc.message,
            path=str(request.url),
            details=exc.details,
        )
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": exc.error_code,
                "message": exc.message,
                "details": exc.details,
            },
        )

    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("unhandled_exception", path=str(request.url))
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "INTERNAL_ERROR",
                "message": "An unexpected error occurred",
            },
        )
