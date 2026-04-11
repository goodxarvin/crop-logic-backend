from copy import deepcopy

from .mock_data import RISK_SUMMARY_RESPONSE_DATA


def get_risk_summary_data(farm=None):
    return deepcopy(RISK_SUMMARY_RESPONSE_DATA)
