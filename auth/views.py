import secrets

from django.conf import settings
from django.core.cache import cache
from django.core.signing import BadSignature, SignatureExpired, TimestampSigner
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from account.models import User
from .serializers import RequestOTPSerializer, VerifyOTPSerializer
from .sms_service import send_otp_sms


OTP_TTL_SECONDS = 300
OTP_SIGNER = TimestampSigner(salt="auth.otp")


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

        sms_sent = send_otp_sms(phone_number, otp_code)

        payload = {"code": 200, "msg": "success", "token": otp_token}
        if not sms_sent:
            payload["sms_warning"] = "SMS delivery failed; OTP stored server-side."
        if settings.DEBUG:
            payload["debug_otp"] = otp_code

        return Response(payload, status=status.HTTP_200_OK)

    def _verify_otp(self, request):
        serializer = VerifyOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        token = serializer.validated_data["token"]
        otp_code = serializer.validated_data["otp_code"].strip()

        try:
            phone_number = OTP_SIGNER.unsign(
                token, max_age=OTP_TTL_SECONDS
            )
        except (BadSignature, SignatureExpired):
            return Response(
                {"code": 400, "msg": "Token is invalid or expired."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        cached_otp = cache.get(f"otp_code:{phone_number}")
        if cached_otp is None or cached_otp != otp_code:
            return Response(
                {"code": 400, "msg": "OTP code is invalid or expired."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        cache.delete(f"otp_code:{phone_number}")

        user, created = User.objects.get_or_create(
            phone_number=phone_number,
            defaults={"username": phone_number},
        )

        refresh = RefreshToken.for_user(user)

        user_data = _auth_user_to_data(user)

        return Response(
            {
                "code": 200,
                "msg": "success",
                "data": user_data,
                "token": {
                    "access": str(refresh.access_token),
                    "refresh": str(refresh),
                },
            },
            status=status.HTTP_200_OK,
        )
