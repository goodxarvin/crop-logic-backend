from __future__ import annotations

from typing import Any

from access_control.catalog import GOLD_PLAN_CODE

from .models import SubscriptionPlan


def get_default_subscription_plan() -> SubscriptionPlan | None:
    return SubscriptionPlan.objects.filter(is_active=True, metadata__is_default=True).order_by("name").first()


def get_effective_subscription_plan(farm: Any) -> SubscriptionPlan | None:
    if farm is None:
        return get_default_subscription_plan()

    if getattr(farm, "subscription_plan_id", None):
        return farm.subscription_plan

    default_plan = get_default_subscription_plan()
    if default_plan is not None:
        return default_plan

    return SubscriptionPlan.objects.filter(code=GOLD_PLAN_CODE, is_active=True).order_by("name").first()

