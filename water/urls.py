from django.urls import path

from .views import FarmWeatherCardView, WaterNeedPredictionView, WaterStressIndexView, WaterSummaryView

urlpatterns = [
    path("card/", FarmWeatherCardView.as_view(), name="water-card"),
    path("need-prediction/", WaterNeedPredictionView.as_view(), name="water-need-prediction"),
    path("stress-index/", WaterStressIndexView.as_view(), name="water-stress-index"),
    path("summary/", WaterSummaryView.as_view(), name="water-summary"),
]
