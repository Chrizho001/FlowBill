import structlog
from rest_framework.exceptions import Throttled
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status

logger = structlog.get_logger(__name__)


def flowbill_exception_handler(exc, context):
    """
    Custom exception handler that returns consistent JSON error responses.

    All errors follow this shape:
    {
        "status": "error",
        "code": "ERROR_CODE",
        "message": "Human readable message",
        "fields": {}   # populated on validation errors only
    }
    """
    response = exception_handler(exc, context)
    request = context.get("request") if context else None
    view = context.get("view") if context else None

    if response is None:
        logger.error(
            "api.unhandled_exception",
            exc_type=type(exc).__name__,
            error=str(exc),
            path=request.path if request else None,
            view=type(view).__name__ if view else None,
            exc_info=True,
        )
        return Response(
            {
                "status": "error",
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred.",
                "fields": {},
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    logger.warning(
        "api.error",
        status_code=response.status_code,
        exc_type=type(exc).__name__,
        path=request.path if request else None,
        view=type(view).__name__ if view else None,
    )

    error_payload = {
        "status": "error",
        "code": _get_error_code(exc, response),
        "message": _get_error_message(exc, response),
        "fields": {},
    }

    # Validation errors — include field-level detail
    if response.status_code == status.HTTP_400_BAD_REQUEST:
        if hasattr(response, "data") and isinstance(response.data, dict):
            fields = {}
            for field, errors in response.data.items():
                if field not in ("detail", "non_field_errors"):
                    fields[field] = (
                        [str(e) for e in errors]
                        if isinstance(errors, list)
                        else [str(errors)]
                    )
            error_payload["fields"] = fields
            if "non_field_errors" in response.data:
                error_payload["message"] = str(response.data["non_field_errors"][0])
        error_payload["code"] = "VALIDATION_ERROR"

    response.data = error_payload

    # Throttled responses — tell the client when the window resets
    if response.status_code == 429 and isinstance(exc, Throttled) and exc.wait is not None:
        response["Retry-After"] = str(int(exc.wait))

    return response


def _get_error_code(exc, response):
    code_map = {
        400: "VALIDATION_ERROR",
        401: "AUTHENTICATION_REQUIRED",
        403: "PERMISSION_DENIED",
        404: "NOT_FOUND",
        405: "METHOD_NOT_ALLOWED",
        429: "RATE_LIMIT_EXCEEDED",
        500: "INTERNAL_SERVER_ERROR",
    }
    return code_map.get(response.status_code, "ERROR")


def _get_error_message(exc, response):
    if hasattr(exc, "detail"):
        detail = exc.detail
        if isinstance(detail, list) and detail:
            return str(detail[0])
        if isinstance(detail, dict) and "detail" in detail:
            return str(detail["detail"])
        return str(detail)
    return "An unexpected error occurred"