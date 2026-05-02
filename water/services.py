from copy import deepcopy

from irrigation.models import IrrigationRecommendationRequest

from .mock_data import FARM_WEATHER_CARD, WATER_NEED_PREDICTION, WATER_STRESS_INDEX
from .models import WeatherForecastLog


def get_farm_weather_card_data(farm=None):
    if farm is None:
        return deepcopy(FARM_WEATHER_CARD)

    log = WeatherForecastLog.objects.filter(farm=farm).first()
    if log is None:
        return deepcopy(FARM_WEATHER_CARD)

    return {
        "condition": log.condition or FARM_WEATHER_CARD["condition"],
        "temperature": log.temperature if log.temperature is not None else FARM_WEATHER_CARD["temperature"],
        "unit": log.unit or FARM_WEATHER_CARD["unit"],
        "humidity": log.humidity if log.humidity is not None else FARM_WEATHER_CARD["humidity"],
        "windSpeed": log.wind_speed if log.wind_speed is not None else FARM_WEATHER_CARD["windSpeed"],
        "windUnit": log.wind_unit or FARM_WEATHER_CARD["windUnit"],
        "chartData": deepcopy(log.chart_data or FARM_WEATHER_CARD["chartData"]),
    }


def _extract_irrigation_result(response_payload):
    if not isinstance(response_payload, dict):
        return {}

    data = response_payload.get("data")
    if isinstance(data, dict) and isinstance(data.get("result"), dict):
        return data["result"]

    result = response_payload.get("result")
    if isinstance(result, dict):
        return result

    return {}


def _get_latest_irrigation_result(farm):
    if farm is None:
        return {}

    for request in IrrigationRecommendationRequest.objects.filter(farm=farm):
        result = _extract_irrigation_result(request.response_payload)
        if result:
            return result

    return {}


def get_water_need_prediction_data(farm=None):
    default_data = deepcopy(WATER_NEED_PREDICTION)
    result = _get_latest_irrigation_result(farm)
    water_balance = result.get("water_balance", {})
    daily = water_balance.get("daily", [])

    if not daily:
        return default_data

    categories = [item.get("forecast_date") or f"روز {index + 1}" for index, item in enumerate(daily)]
    series_data = [float(item.get("gross_irrigation_mm") or 0) for item in daily]

    return {
        "totalNext7Days": round(sum(series_data), 2),
        "unit": "mm",
        "categories": categories,
        "series": [{"name": "نیاز آبی", "data": series_data}],
    }


def get_water_stress_index_data(farm=None):
    data = deepcopy(WATER_STRESS_INDEX)
    result = _get_latest_irrigation_result(farm)
    moisture_level = (result.get("plan") or {}).get("moistureLevel")

    if moisture_level is None:
        return data

    stress_value = max(0, round(80 - float(moisture_level)))
    if stress_value <= 15:
        data["chipText"] = "پایین"
        data["chipColor"] = "success"
        data["avatarColor"] = "info"
    elif stress_value <= 30:
        data["chipText"] = "متوسط"
        data["chipColor"] = "warning"
        data["avatarColor"] = "warning"
    else:
        data["chipText"] = "بالا"
        data["chipColor"] = "error"
        data["avatarColor"] = "error"

    data["stats"] = f"{stress_value}%"
    return data


def get_water_summary_data(farm=None):
    return {
        "farmWeatherCard": get_farm_weather_card_data(farm),
        "waterNeedPrediction": get_water_need_prediction_data(farm),
        "waterStressIndex": get_water_stress_index_data(farm),
    }
