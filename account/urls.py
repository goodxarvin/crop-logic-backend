from django.urls import path

from .views import AccountView, ProfileView

urlpatterns = [
    path("profile/", ProfileView.as_view(), name="profile-update"),
    path("<uuid:uuid>/", AccountView.as_view(), name="account-detail"),
    path("", AccountView.as_view(), name="account-list"),
]
