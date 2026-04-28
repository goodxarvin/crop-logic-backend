from django.urls import path

from .views import (
    Sensor7In1SummaryView,
)


urlpatterns = [
    path("summary/", Sensor7In1SummaryView.as_view(), name="sensor-7-in-1-summary"),
]
