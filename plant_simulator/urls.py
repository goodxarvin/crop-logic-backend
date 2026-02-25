from django.urls import path

from .views import (
    ConfigView,
    EnvironmentView,
    ResetView,
    StartView,
    StateView,
    StopView,
)

urlpatterns = [
    path("config/", ConfigView.as_view(), name="plant-simulator-config"),
    path("state/", StateView.as_view(), name="plant-simulator-state"),
    path("start/", StartView.as_view(), name="plant-simulator-start"),
    path("stop/", StopView.as_view(), name="plant-simulator-stop"),
    path("reset/", ResetView.as_view(), name="plant-simulator-reset"),
    path("environment/", EnvironmentView.as_view(), name="plant-simulator-environment"),
]
