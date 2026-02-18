import secrets

from django.conf import settings
from django.core.cache import cache
from django.core.signing import TimestampSigner
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import RequestOTPSerializer, VerifyOTPSerializer


OTP_TTL_SECONDS = 300
OTP_SIGNER = TimestampSigner(salt="auth.otp")


def _auth_user_to_data(user):
    """Build AuthUser-shaped dict from Django User (or mock)."""
    # if user is None or not getattr(user, "pk", None):
    #     return None
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


class AuthenticationView(APIView):
    """
    Single view for auth flows: request-otp and verify-otp.
    Dispatches by path: .../request-otp/ -> request_otp, .../verify-otp/ -> verify_otp.
    Response format: RequestOTPResponse / VerifyOTPResponse (code, msg, token, data when applicable).
    """

    def post(self, request):
        if "verify-otp" in request.path:
            return self._verify_otp(request)
        return self._request_otp(request)

    def _request_otp(self, request):
        serializer = RequestOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        phone_number = serializer.validated_data["phone_number"].strip()
        otp_code = f"{secrets.randbelow(1_000_000):06d}"

        cache.set(f"otp_code:{phone_number}", otp_code, timeout=OTP_TTL_SECONDS)
        otp_token = OTP_SIGNER.sign(phone_number)

        payload = {"code": 200, "msg": "success", "token": otp_token}
        if settings.DEBUG:
            payload["debug_note"] = "OTP code is returned only when DEBUG=1."

        return Response(payload, status=status.HTTP_200_OK)

    def _verify_otp(self, request):
        serializer = VerifyOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # TODO: validate token + otp_code, load or create user, issue JWT/session token
        auth_token = "1234567890"
        user_data = _auth_user_to_data(getattr(request, "user", None))
        if user_data is None:
            user_data = {
                "id": 0,
                "username": "",
                "email": "",
                "first_name": "",
                "last_name": "",
                "phone_number": "",
            }

        return Response(
            {
                "code": 200,
                "msg": "success",
                "data": user_data,
                "token": auth_token,
            },
            status=status.HTTP_200_OK,
        )

