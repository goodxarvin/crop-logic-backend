from copy import deepcopy

from .defaults import EMPTY_ECONOMIC_OVERVIEW
from .models import EconomicOverviewLog


def get_economic_overview_data(farm=None):
    data = deepcopy(EMPTY_ECONOMIC_OVERVIEW)

    if farm is None:
        return data

    log = EconomicOverviewLog.objects.filter(farm=farm).first()
    if log is None:
        return data

    data["status"] = "success"
    data["source"] = "db"
    data["warnings"] = []
    if log.economic_data:
        data["economicData"] = deepcopy(log.economic_data)
    if log.chart_series:
        data["chartSeries"] = deepcopy(log.chart_series)
    if log.chart_categories:
        data["chartCategories"] = deepcopy(log.chart_categories)

    return data
