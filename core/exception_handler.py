from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler

from core.exceptions import EmailAlreadyExistsError, InvalidCredentialsError, WeakPasswordError

_EXCEPTION_MAP = {
    InvalidCredentialsError: status.HTTP_400_BAD_REQUEST,
    EmailAlreadyExistsError: status.HTTP_409_CONFLICT,
    WeakPasswordError: status.HTTP_400_BAD_REQUEST,
}


def custom_exception_handler(exc, context):
    for exc_class, status_code in _EXCEPTION_MAP.items():
        if isinstance(exc, exc_class):
            return Response({"detail": str(exc)}, status=status_code)

    return exception_handler(exc, context)
