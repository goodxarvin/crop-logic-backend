from django.urls import path

from .views import FarmWeatherCardView

urlpatterns = [
    path("card/", FarmWeatherCardView.as_view(), name="weather-forecast-card"),
]
