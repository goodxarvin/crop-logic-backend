from rest_framework import status
from rest_framework.exceptions import AuthenticationFailed, NotAuthenticated, PermissionDenied
from rest_framework.views import exception_handler as drf_exception_handler


def custom_exception_handler(exc, context):
    response = drf_exception_handler(exc, context)
    if response is None:
        return None

    if isinstance(exc, PermissionDenied):
        detail = response.data.get("detail", "Access denied.")
        response.data = {"code": status.HTTP_403_FORBIDDEN, "msg": "error", "data": {"detail": detail}}
        return response

    if isinstance(exc, (NotAuthenticated, AuthenticationFailed)):
        detail = response.data.get("detail", "Authentication credentials were not provided.")
        response.data = {"code": response.status_code, "msg": "error", "data": {"detail": detail}}
        return response

    return response
