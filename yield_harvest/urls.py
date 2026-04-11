from django.urls import path

from .views import (
    ConfigView,
    EnvironmentView,
    ResetView,
    StartView,
    StateView,
    StopView,
    YieldHarvestSummaryView,
)

ConfigView.__module__ = "plant_simulator.views"
EnvironmentView.__module__ = "plant_simulator.views"
ResetView.__module__ = "plant_simulator.views"
StartView.__module__ = "plant_simulator.views"
StateView.__module__ = "plant_simulator.views"
StopView.__module__ = "plant_simulator.views"

plant_simulator_urlpatterns = [
    path("config/", ConfigView.as_view(), name="plant-simulator-config"),
    path("state/", StateView.as_view(), name="plant-simulator-state"),
    path("start/", StartView.as_view(), name="plant-simulator-start"),
    path("stop/", StopView.as_view(), name="plant-simulator-stop"),
    path("reset/", ResetView.as_view(), name="plant-simulator-reset"),
    path("environment/", EnvironmentView.as_view(), name="plant-simulator-environment"),
]

urlpatterns = [
    path("summary/", YieldHarvestSummaryView.as_view(), name="yield-harvest-summary"),
]
