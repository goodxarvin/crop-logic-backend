from django.urls import path

from .views import AuthenticationView

urlpatterns = [
    path("request-otp/", AuthenticationView.as_view(), name="request-otp"),
    path("verify-otp/", AuthenticationView.as_view(), name="verify-otp"),
]

