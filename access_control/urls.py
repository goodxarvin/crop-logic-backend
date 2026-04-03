from django.urls import path

from .views import FarmAccessProfileView, SubscriptionPlanListView


urlpatterns = [
    path("subscription-plans/", SubscriptionPlanListView.as_view(), name="subscription-plan-list"),
    path("farms/<uuid:farm_uuid>/profile/", FarmAccessProfileView.as_view(), name="farm-access-profile"),
]

