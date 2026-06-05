import logging

from rest_framework import status
from rest_framework.response import Response
from rest_framework.serializers import ValidationError as DRFValidationError
from rest_framework.exceptions import (
    AuthenticationFailed,
    NotAuthenticated,
    PermissionDenied,
    NotFound,
    APIException,
    MethodNotAllowed,
    UnsupportedMediaType,
    Throttled,
)
from django.http import Http404
from django.db import IntegrityError
from django.core.exceptions import ValidationError as DjangoValidationError
from django.utils import timezone

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    if isinstance(exc, DRFValidationError):
        return Response(
            {
                "success": False,
                "message": "Validation failed",
                "error_code": "VALIDATION_ERROR",
                "errors": exc.detail,
                "timestamp": timezone.now().isoformat(),
                "status_code": status.HTTP_400_BAD_REQUEST,
            },
            status=status.HTTP_400_BAD_REQUEST,
        )
    if isinstance(exc, DjangoValidationError):
        return Response(
            {
                "success": False,
                "message": "Validation failed",
                "error_code": "VALIDATION_ERROR",
                "errors": exc.message_dict if hasattr(exc, 'message_dict') else str(exc),
                "timestamp": timezone.now().isoformat(),
                "status_code": status.HTTP_400_BAD_REQUEST,
            },
            status=status.HTTP_400_BAD_REQUEST,
        )
    if isinstance(exc, NotAuthenticated):
        return Response(
            {
                "success": False,
                "message": "Authentication credentials were not provided.",
                "error_code": "NOT_AUTHENTICATED",
                "timestamp": timezone.now().isoformat(),
                "status_code": status.HTTP_401_UNAUTHORIZED,
            },
            status=status.HTTP_401_UNAUTHORIZED,
        )
    if isinstance(exc, AuthenticationFailed):
        return Response(
            {
                "success": False,
                "message": "Invalid authentication credentials.",
                "error_code": "AUTHENTICATION_FAILED",
                "timestamp": timezone.now().isoformat(),
                "status_code": status.HTTP_401_UNAUTHORIZED,
            },
            status=status.HTTP_401_UNAUTHORIZED,
        )
    if isinstance(exc, PermissionDenied):
        return Response(
            {
                "success": False,
                "message": "You do not have permission to perform this action.",
                "error_code": "PERMISSION_DENIED",
                "timestamp": timezone.now().isoformat(),
                "status_code": status.HTTP_403_FORBIDDEN,
            },
            status=status.HTTP_403_FORBIDDEN,
        )
    if isinstance(exc, (NotFound, Http404)):
        return Response(
            {
                "success": False,
                "message": "The requested resource was not found.",
                "error_code": "RESOURCE_NOT_FOUND",
                "timestamp": timezone.now().isoformat(),
                "status_code": status.HTTP_404_NOT_FOUND,
            },
            status=status.HTTP_404_NOT_FOUND,
        )
    if isinstance(exc, MethodNotAllowed):
        return Response(
            {
                "success": False,
                "message": f"Method '{exc.method}' not allowed.",
                "error_code": "METHOD_NOT_ALLOWED",
                "timestamp": timezone.now().isoformat(),
                "status_code": status.HTTP_405_METHOD_NOT_ALLOWED,
            },
            status=status.HTTP_405_METHOD_NOT_ALLOWED,
        )
    if isinstance(exc, UnsupportedMediaType):
        return Response(
            {
                "success": False,
                "message": "Unsupported media type in request.",
                "error_code": "UNSUPPORTED_MEDIA_TYPE",
                "timestamp": timezone.now().isoformat(),
                "status_code": status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            },
            status=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
        )
    if isinstance(exc, Throttled):
        return Response(
            {
                "success": False,
                "message": f"Request was throttled. Expected available in {exc.wait} seconds.",
                "error_code": "RATE_LIMITED",
                "timestamp": timezone.now().isoformat(),
                "status_code": status.HTTP_429_TOO_MANY_REQUESTS,
                "retry_after": exc.wait,
            },
            status=status.HTTP_429_TOO_MANY_REQUESTS,
        )
    if isinstance(exc, IntegrityError):
        return Response(
            {
                "success": False,
                "message": "Data integrity constraint violation.",
                "error_code": "INTEGRITY_ERROR",
                "timestamp": timezone.now().isoformat(),
                "status_code": status.HTTP_409_CONFLICT,
            },
            status=status.HTTP_409_CONFLICT,
        )
    if isinstance(exc, APIException):
        return Response(
            {
                "success": False,
                "message": str(exc.detail),
                "error_code": "API_EXCEPTION",
                "timestamp": timezone.now().isoformat(),
                "status_code": exc.status_code,
            },
            status=exc.status_code,
        )

    logger.error(f"Unhandled exception: {type(exc).__name__}: {str(exc)}")
    return Response(
        {
            "success": False,
            "message": "An unexpected error occurred. Please try again later.",
            "error_code": "INTERNAL_ERROR",
            "timestamp": timezone.now().isoformat(),
            "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
        },
        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )


class BaseResponseMixin:

    def success_response(self, data=None, message="Success",
                         status_code=status.HTTP_200_OK, **kwargs):
        response_data = {
            "success": True,
            "message": message,
            "timestamp": timezone.now().isoformat(),
            "status_code": status_code,
        }
        if data is not None:
            response_data["data"] = data
        response_data.update(kwargs)
        return Response(response_data, status=status_code)

    def error_response(self, message="Error", error_code=None, errors=None,
                       status_code=status.HTTP_400_BAD_REQUEST, **kwargs):
        response_data = {
            "success": False,
            "message": message,
            "timestamp": timezone.now().isoformat(),
            "status_code": status_code,
        }
        if error_code:
            response_data["error_code"] = error_code
        if errors:
            response_data["errors"] = errors
        response_data.update(kwargs)
        return Response(response_data, status=status_code)

    def created_response(self, data=None, message="Resource created successfully"):
        return self.success_response(
            data=data, message=message, status_code=status.HTTP_201_CREATED
        )

    def updated_response(self, data=None, message="Resource updated successfully"):
        return self.success_response(
            data=data, message=message, status_code=status.HTTP_200_OK
        )

    def deleted_response(self, message="Resource deleted successfully"):
        return self.success_response(
            message=message, status_code=status.HTTP_204_NO_CONTENT
        )

    def not_found_response(self, message="Resource not found"):
        return self.error_response(
            message=message, error_code="RESOURCE_NOT_FOUND",
            status_code=status.HTTP_404_NOT_FOUND
        )

    def bad_request_response(self, message="Bad request", errors=None):
        return self.error_response(
            message=message, error_code="BAD_REQUEST",
            errors=errors, status_code=status.HTTP_400_BAD_REQUEST
        )
