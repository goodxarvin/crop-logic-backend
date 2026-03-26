from django.urls import path

from .views import SensorActiveView, SensorDeactiveView, SensorDetailView, SensorListCreateView

urlpatterns = [
    path("active/", SensorActiveView.as_view(), name="sensor-hub-active"),
    path("deactive/", SensorDeactiveView.as_view(), name="sensor-hub-deactive"),
    path("<uuid:uuid>/", SensorDetailView.as_view(), name="sensor-hub-detail"),
    path("", SensorListCreateView.as_view(), name="sensor-hub-list"),
]
