from collections import Counter
from copy import deepcopy

from farm_hub.models import FarmHub
from notifications.models import FarmNotification

from .mock_data import (
    ANOMALY_DETECTION_CARD,
    ARM_ALERTS_TRACKER,
    FARM_ALERTS_TIMELINE,
    RECOMMENDATIONS_LIST,
)
from .models import AnomalyDetection, FarmAlert, Recommendation


class AlertService:
    @staticmethod
    def create_alert(
        title: str,
        description: str = "",
        color: str = "info",
        avatar_icon: str = "",
        avatar_color: str = "",
        farm_uuid=None,
    ) -> FarmAlert:
        farm = None
        if farm_uuid:
            try:
                farm = FarmHub.objects.get(uuid=farm_uuid)
            except FarmHub.DoesNotExist:
                pass

        alert = FarmAlert.objects.create(
            farm=farm,
            title=title,
            description=description,
            color=color,
            avatar_icon=avatar_icon,
            avatar_color=avatar_color,
        )

        AlertService._send_notification(alert, farm)
        return alert

    @staticmethod
    def _send_notification(alert: FarmAlert, farm) -> None:
        if farm is None:
            return

        level_map = {"error": "error", "warning": "warning", "info": "info", "success": "success"}

        FarmNotification.objects.create(
            farm=farm,
            title=alert.title,
            message=alert.description,
            level=level_map.get(alert.color, "info"),
            metadata={"alert_uuid": str(alert.uuid), "color": alert.color},
        )


def get_alert_tracker_data(farm=None):
    if farm is None:
        return deepcopy(ARM_ALERTS_TRACKER)

    alerts = list(FarmAlert.objects.filter(farm=farm, is_active=True)[:20])
    if not alerts:
        return deepcopy(ARM_ALERTS_TRACKER)

    counts = Counter(alert.title for alert in alerts)
    alert_stats = []
    for title, count in counts.most_common(3):
        sample = next((alert for alert in alerts if alert.title == title), None)
        alert_stats.append(
            {
                "title": title,
                "count": str(count),
                "avatarColor": sample.color if sample else "info",
                "avatarIcon": sample.avatar_icon or "tabler-bell",
            }
        )

    return {
        "totalAlerts": len(alerts),
        "radialBarValue": min(len(alerts) * 10, 100),
        "alertStats": alert_stats,
    }


def get_alert_timeline_data(farm=None):
    if farm is None:
        return deepcopy(FARM_ALERTS_TIMELINE)

    alerts = list(FarmAlert.objects.filter(farm=farm)[:10])
    if not alerts:
        return deepcopy(FARM_ALERTS_TIMELINE)

    return {
        "alerts": [
            {
                "title": alert.title,
                "description": alert.description,
                "time": alert.created_at.strftime("%Y-%m-%d %H:%M"),
                "color": alert.color,
            }
            for alert in alerts
        ]
    }


def get_anomaly_detection_data(farm=None):
    if farm is None:
        return deepcopy(ANOMALY_DETECTION_CARD)

    anomalies = list(AnomalyDetection.objects.filter(farm=farm)[:10])
    if not anomalies:
        return deepcopy(ANOMALY_DETECTION_CARD)

    return {
        "anomalies": [
            {
                "sensor": anomaly.sensor,
                "value": anomaly.value,
                "expected": anomaly.expected,
                "deviation": anomaly.deviation,
                "severity": anomaly.severity,
            }
            for anomaly in anomalies
        ]
    }


def get_recommendations_list_data(farm=None):
    if farm is None:
        return deepcopy(RECOMMENDATIONS_LIST)

    recommendations = list(Recommendation.objects.filter(farm=farm)[:10])
    if not recommendations:
        return deepcopy(RECOMMENDATIONS_LIST)

    return {
        "recommendations": [
            {
                "title": recommendation.title,
                "subtitle": recommendation.subtitle,
                "avatarIcon": recommendation.avatar_icon or "tabler-bulb",
                "avatarColor": recommendation.avatar_color or "info",
            }
            for recommendation in recommendations
        ]
    }
