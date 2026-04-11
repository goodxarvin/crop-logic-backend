from copy import deepcopy

from .mock_data import FARM_HEALTH_SCORE, NDVI_HEALTH_CARD


def get_crop_health_summary_data(farm=None):
    return {
        "ndviHealthCard": deepcopy(NDVI_HEALTH_CARD),
        "farmHealthScore": deepcopy(FARM_HEALTH_SCORE),
    }
