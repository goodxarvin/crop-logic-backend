from rest_framework import serializers


# --- Register ---
class RegisterSerializer(serializers.Serializer):
    """Request body for POST /api/auth/register/."""

    username = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    phone_number = serializers.CharField(max_length=32)
    password = serializers.CharField(min_length=8, write_only=True)
    first_name = serializers.CharField(max_length=150, required=False, default="")
    last_name = serializers.CharField(max_length=150, required=False, default="")


# --- Login ---
class LoginSerializer(serializers.Serializer):
    """Request body for POST /api/auth/login/.
    identifier can be username, email, or phone_number."""

    identifier = serializers.CharField()
    password = serializers.CharField(min_length=8, write_only=True)


# --- RequestOTP (request-otp/) ---
class RequestOTPSerializer(serializers.Serializer):
    """Request body for POST /api/auth/request-otp/."""

    phone_number = serializers.CharField(max_length=32)


# --- VerifyOTP (verify-otp/) ---
class VerifyOTPSerializer(serializers.Serializer):
    """Request body for POST /api/auth/verify-otp/."""

    token = serializers.CharField()
    otp_code = serializers.CharField(max_length=10)


# --- AuthUser (used in VerifyOTPResponse and UpdateProfileResponse) ---
class AuthUserSerializer(serializers.Serializer):
    """User data returned in auth/account responses."""

    id = serializers.IntegerField()
    username = serializers.CharField()
    email = serializers.EmailField(allow_blank=True)
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    phone_number = serializers.CharField()
