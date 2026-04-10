from django.urls import path

from .views import YieldHarvestSummaryView

urlpatterns = [
    path("summary/", YieldHarvestSummaryView.as_view(), name="yield-harvest-summary"),
]
