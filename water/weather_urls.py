from django.urls import path

from .views import WeatherFarmCardView

urlpatterns = [
    path("farm-card/", WeatherFarmCardView.as_view(), name="weather-farm-card"),
]
