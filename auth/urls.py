from django.urls import path

from .views import AuthenticationView, LoginView, RegisterView

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("login/", LoginView.as_view(), name="login"),
    # path("request-otp/", AuthenticationView.as_view(), name="request-otp"),
    # path("verify-otp/", AuthenticationView.as_view(), name="verify-otp"),
]
