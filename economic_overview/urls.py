from django.urls import path

from .views import EconomicOverviewView

urlpatterns = [
    path("summary/", EconomicOverviewView.as_view(), name="economic-overview-summary"),
]
