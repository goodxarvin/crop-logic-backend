from django.urls import path

from .views import EconomyOverviewView

urlpatterns = [
    path("overview/", EconomyOverviewView.as_view(), name="economy-overview"),
]
