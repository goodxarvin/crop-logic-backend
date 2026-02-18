from django.urls import path

from .views import SensorHubView

urlpatterns = [
    path("active/", SensorHubView.as_view(), name="sensor-hub-active", kwargs={"action": "active"}),
    path("deactive/", SensorHubView.as_view(), name="sensor-hub-deactive", kwargs={"action": "deactive"}),
    path("<uuid:uuid>/", SensorHubView.as_view(), name="sensor-hub-detail"),
    path("", SensorHubView.as_view(), name="sensor-hub-list"),
]
