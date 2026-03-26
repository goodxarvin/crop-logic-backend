from django.urls import path

from .views import FarmDashboardCardsView

urlpatterns = [
    # path("cards/", FarmDashboardCardsView.as_view(), name="farm-dashboard-cards"),
    path("", FarmDashboardCardsView.as_view(), name="farm-dashboard"),
]
