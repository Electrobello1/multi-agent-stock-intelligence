import logging

from fastapi import (
    Request,
    status
)
from fastapi.exceptions import (
    RequestValidationError
)
from fastapi.responses import JSONResponse

from Backend.Resilience.circuit_breaker import (
    CircuitOpenError
)


logger = logging.getLogger(__name__)


def register_exception_handlers(app):
    """
    Register all global FastAPI exception handlers.
    """

    app.add_exception_handler(
        RequestValidationError,
        validation_exception_handler
    )

    app.add_exception_handler(
        CircuitOpenError,
        circuit_open_exception_handler
    )

    app.add_exception_handler(
        ValueError,
        value_error_handler
    )

    app.add_exception_handler(
        Exception,
        generic_exception_handler
    )


async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError
):
    """
    Handle Pydantic/FastAPI request validation errors.
    """

    logger.warning(
        "Request validation failed: %s %s - %s",
        request.method,
        request.url.path,
        exc.errors()
    )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Request validation failed.",
                "details": exc.errors()
            }
        }
    )


async def circuit_open_exception_handler(
    request: Request,
    exc: CircuitOpenError
):
    """
    Handle circuit-breaker failures.

    Internal circuit names are intentionally not exposed
    to the client.
    """

    logger.warning(
        "Circuit breaker open: %s %s - %s",
        request.method,
        request.url.path,
        str(exc)
    )

    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={
            "error": {
                "code": "SERVICE_UNAVAILABLE",
                "message": (
                    "A required service is temporarily "
                    "unavailable. Please try again later."
                )
            }
        },
        headers={
            "Retry-After": "30"
        }
    )


async def value_error_handler(
    request: Request,
    exc: ValueError
):
    """
    Handle expected application-level ValueErrors.

    The exception message is returned because these errors
    represent controlled client/application validation failures.
    """

    logger.warning(
        "Application error: %s %s - %s",
        request.method,
        request.url.path,
        str(exc)
    )

    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "error": {
                "code": "BAD_REQUEST",
                "message": str(exc)
            }
        }
    )


async def generic_exception_handler(
    request: Request,
    exc: Exception
):
    """
    Catch-all handler for unexpected server errors.

    Never expose the underlying exception to the client.
    """

    logger.exception(
        "Unhandled API exception: %s %s",
        request.method,
        request.url.path
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": (
                    "An unexpected error occurred. "
                    "Please try again later."
                )
            }
        }
    )