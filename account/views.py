"""
Account API module.
CRUD endpoints for user account profile.
"""

from rest_framework import serializers
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, extend_schema_view

from auth.serializers import AuthUserSerializer
from config.swagger import code_response
from .serializers import UpdateProfileSerializer


def _auth_user_to_data(user):
    """Build AuthUser-shaped dict from Django User."""
    if user is None or not getattr(user, "pk", None):
        return None
    return {
        "id": user.id,
        "username": getattr(user, "username", "") or "",
        "email": getattr(user, "email", "") or "",
        "first_name": getattr(user, "first_name", "") or "",
        "last_name": getattr(user, "last_name", "") or "",
        "phone_number": getattr(user, "phone_number", "") or "",
    }


@extend_schema_view(
    patch=extend_schema(
        tags=["Account"],
        request=UpdateProfileSerializer,
        responses={200: code_response("ProfileUpdateResponse", data=AuthUserSerializer())},
    ),
)
class ProfileView(APIView):
    """
    PATCH /api/account/profile/
    UpdateProfilePayload: first_name, last_name, email.
    UpdateProfileResponse: code, msg, data (AuthUser).
    """

    permission_classes = [IsAuthenticated]

    def patch(self, request):
        serializer = UpdateProfileSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        user = request.user
        for field in ("first_name", "last_name", "email"):
            if field in serializer.validated_data:
                setattr(user, field, serializer.validated_data[field])
        user.save(update_fields=[
            f for f in ("first_name", "last_name", "email")
            if f in serializer.validated_data
        ])

        data = _auth_user_to_data(user)
        if data is None:
            data = {
                "id": 0,
                "username": "",
                "email": "",
                "first_name": "",
                "last_name": "",
                "phone_number": "",
            }
        return Response(
            {"code": 200, "msg": "success", "data": data},
            status=status.HTTP_200_OK,
        )


@extend_schema_view(
    get=extend_schema(
        tags=["Account"],
        responses={200: code_response("AccountGetResponse", data=serializers.JSONField())},
    ),
    post=extend_schema(
        tags=["Account"],
        request=OpenApiTypes.OBJECT,
        responses={200: code_response("AccountCreateResponse")},
    ),
    patch=extend_schema(
        tags=["Account"],
        request=OpenApiTypes.OBJECT,
        responses={200: code_response("AccountUpdateResponse")},
    ),
    delete=extend_schema(
        tags=["Account"],
        responses={200: code_response("AccountDeleteResponse")},
    ),
)
class AccountView(APIView):
    """
    Account CRUD endpoints. Dispatch by HTTP method and path (uuid for detail/update/delete).
    No processing, validation, or transformation is applied to any input.
    All endpoints return HTTP 200 only. Response format: {"code": 200, "msg": "success"} or {"code": 200, "msg": "success", "data": {}}.

    Routes:
    - GET    ""         → List: returns status "success", data {}.
    - GET    "<uuid>/"  → Detail: uuid (path). Returns status "success", data {}.
    - POST   ""         → Create: body/query may contain first_name, last_name, phones; not used. Returns status "success". No data field.
    - PATCH  "<uuid>/"  → Update: uuid (path), body/query may contain first_name, last_name, phones; not used. Returns status "success". No data field.
    - DELETE "<uuid>/"  → Delete: uuid (path). Returns status "success". No data field.
    """

    # permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        """
        List or detail account.

        List (GET on base URL):
        - Input parameters: none required. Query params if sent are not processed.
        - Response: {"code": 200, "msg": "success", "data": {}}.
        - No processing or validation is performed on inputs.

        Detail (GET on <uuid>/):
        - Input parameters: uuid (path, UUID). Description: identifier for the account resource.
        - Response: {"code": 200, "msg": "success", "data": {}}.
        - No processing or validation is performed on inputs.
        """
        return Response({"code": 200, "msg": "success", "data": {}}, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        """
        Create account.

        Input parameters (body, JSON): first_name (string), last_name (string), phones (array of strings).
        Description: intended for user first name, last name, and phone numbers. Not processed or validated.
        Response: {"code": 200, "msg": "success"}. No data field.
        No processing or validation is performed on inputs.
        """
        return Response({"code": 200, "msg": "success"}, status=status.HTTP_200_OK)

    def patch(self, request, *args, **kwargs):
        """
        Update account.

        Input parameters: uuid (path, UUID), body (JSON) may contain first_name, last_name, phones.
        Description: identifier in path; body fields intended for updated profile. Not processed or validated.
        Response: {"code": 200, "msg": "success"}. No data field.
        No processing or validation is performed on inputs.
        """
        return Response({"code": 200, "msg": "success"}, status=status.HTTP_200_OK)

    def delete(self, request, *args, **kwargs):
        """
        Delete account.

        Input parameters: uuid (path, UUID). Description: identifier for the account resource to delete.
        Response: {"code": 200, "msg": "success"}. No data field.
        No processing or validation is performed on inputs.
        """
        return Response({"code": 200, "msg": "success"}, status=status.HTTP_200_OK)
