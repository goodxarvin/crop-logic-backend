from django.urls import path

from .views import SensorExternalAPIView

urlpatterns = [
    path("", SensorExternalAPIView.as_view(), name="sensor-external-api"),
]
