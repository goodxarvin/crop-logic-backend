from django.urls import path

from .views import FarmDashboardConfigView

urlpatterns = [
    path("", FarmDashboardConfigView.as_view(), name="farm-dashboard-config"),
]
