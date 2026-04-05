from django.urls import path

from .views import SensorExternalAPIView, SensorExternalRequestLogListAPIView

urlpatterns = [
    path("", SensorExternalAPIView.as_view(), name="sensor-external-api"),
    path("logs/", SensorExternalRequestLogListAPIView.as_view(), name="sensor-external-api-log-list"),
]
