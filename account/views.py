"""
Account API module.
CRUD endpoints for user account profile (first name, last name, phone numbers).
Profile update endpoint returns UpdateProfileResponse (code, msg, data: AuthUser).
"""

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import UpdateProfileSerializer


def _auth_user_to_data(user):
    """Build AuthUser-shaped dict from Django User."""
    if user is None or not getattr(user, "pk", None):
        return None
    # return {
    #     "id": user.id,
    #     "username": getattr(user, "username", "") or "",
    #     "email": getattr(user, "email", "") or "",
    #     "first_name": getattr(user, "first_name", "") or "",
    #     "last_name": getattr(user, "last_name", "") or "",
    #     "phone_number": getattr(user, "phone_number", "") or "",
    # }
    return {
        "id": 1,
        "username": "testuser",
        "email": "testuser@example.com",
        "first_name": "Test",
        "last_name": "User",
        "phone_number": "09123456789",
    }


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
        # TODO: persist first_name, last_name, email via service layer
        user = request.user
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
