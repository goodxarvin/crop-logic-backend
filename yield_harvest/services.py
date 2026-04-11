from copy import deepcopy

from .mock_data import HARVEST_PREDICTION_CARD, YIELD_PREDICTION_CARD, YIELD_PREDICTION_CHART
from .models import YieldHarvestPredictionLog


def get_yield_harvest_summary_data(farm=None):
    data = {
        "yield_prediction_card": deepcopy(YIELD_PREDICTION_CARD),
        "yield_prediction_chart": deepcopy(YIELD_PREDICTION_CHART),
        "harvest_prediction_card": deepcopy(HARVEST_PREDICTION_CARD),
    }

    if farm is None:
        return data

    log = YieldHarvestPredictionLog.objects.filter(farm=farm).first()
    if log is None:
        return data

    if log.yield_stats:
        data["yield_prediction_card"]["stats"] = log.yield_stats
    if log.yield_chip_text:
        data["yield_prediction_card"]["chipText"] = log.yield_chip_text
    if log.chart_data:
        data["yield_prediction_chart"] = deepcopy(log.chart_data)

    if log.harvest_date:
        data["harvest_prediction_card"]["date"] = log.harvest_date.isoformat()
    if log.days_until_harvest is not None:
        data["harvest_prediction_card"]["daysUntil"] = log.days_until_harvest
    if log.optimal_window_start:
        data["harvest_prediction_card"]["optimalWindowStart"] = log.optimal_window_start.isoformat()
    if log.optimal_window_end:
        data["harvest_prediction_card"]["optimalWindowEnd"] = log.optimal_window_end.isoformat()

    return data
