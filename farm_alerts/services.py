from collections import Counter
from copy import deepcopy
import json

from farm_hub.models import FarmHub
from notifications.models import FarmNotification
from notifications.services import create_notification_for_farm_uuid, get_recent_notifications_for_farm

from .mock_data import (
    ANOMALY_DETECTION_CARD,
    ARM_ALERTS_TRACKER,
    FARM_ALERTS_TIMELINE,
    RECOMMENDATIONS_LIST,
)
from .models import AnomalyDetection, FarmAlert, Recommendation


LEVEL_ALIAS_MAP = {
    "danger": "error",
    "critical": "error",
    "warn": "warning",
}


class AlertService:
    @staticmethod
    def normalize_level(level):
        normalized = str(level or "info").strip().lower()
        normalized = LEVEL_ALIAS_MAP.get(normalized, normalized)
        if normalized not in {"info", "warning", "error", "success"}:
            return "info"
        return normalized

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
                farm = FarmHub.objects.get(farm_uuid=farm_uuid)
            except FarmHub.DoesNotExist:
                pass

        alert = FarmAlert.objects.create(
            farm=farm,
            title=title,
            description=description,
            color=AlertService.normalize_level(color),
            avatar_icon=avatar_icon,
            avatar_color=avatar_color,
        )

        AlertService._send_notification(alert, farm)
        return alert

    @staticmethod
    def persist_incoming_alerts(*, farm, alerts):
        saved_alerts = []
        for alert_data in alerts:
            title = alert_data.get("title") or alert_data.get("message") or "Incoming alert"
            level = AlertService.normalize_level(alert_data.get("level"))
            saved_alerts.append(
                FarmAlert.objects.create(
                    farm=farm,
                    external_alert_id=alert_data.get("alert_id", ""),
                    title=title[:255],
                    description=alert_data.get("message", ""),
                    color=level,
                    suggested_action=alert_data.get("suggested_action", ""),
                    source_metric_type=alert_data.get("source_metric_type", ""),
                    occurred_at=alert_data.get("timestamp"),
                    payload=alert_data.get("payload") or {},
                    raw_alert=alert_data,
                    is_active=level != "success",
                )
            )
        return saved_alerts

    @staticmethod
    def _send_notification(alert: FarmAlert, farm) -> None:
        if farm is None:
            return

        FarmNotification.objects.create(
            farm=farm,
            title=alert.title,
            message=alert.description,
            level=alert.color,
            source_alert_id=alert.external_alert_id,
            source_metric_type=alert.source_metric_type,
            suggested_action=alert.suggested_action,
            payload=alert.payload,
            metadata={"alert_uuid": str(alert.uuid), "color": alert.color},
        )


def serialize_notifications_for_ai(*, farm, since_days=3, limit=10):
    notifications = get_recent_notifications_for_farm(farm=farm, since_days=since_days, limit=limit)
    return [
        {
            "id": notification.id,
            "farm_uuid": str(notification.farm.farm_uuid),
            "endpoint": notification.endpoint,
            "level": notification.level,
            "title": notification.title,
            "message": notification.message,
            "suggested_action": notification.suggested_action,
            "source_alert_id": notification.source_alert_id,
            "source_metric_type": notification.source_metric_type,
            "payload": notification.payload,
            "created_at": notification.created_at.isoformat(),
            "updated_at": notification.updated_at.isoformat(),
        }
        for notification in notifications
    ]


def save_tracker_notifications(*, farm_uuid, notifications):
    saved_notifications = []
    for notification_data in notifications:
        title = notification_data.get("title") or ""
        message = notification_data.get("message") or ""
        if not title and not message:
            continue

        source_alert_id = notification_data.get("source_alert_id", "")
        existing = FarmNotification.objects.filter(
            farm__farm_uuid=farm_uuid,
            endpoint="tracker",
            title=title,
            message=message,
            source_alert_id=source_alert_id,
        ).first()
        if existing:
            saved_notifications.append(existing)
            continue

        saved_notifications.append(
            create_notification_for_farm_uuid(
                farm_uuid=farm_uuid,
                endpoint="tracker",
                title=title,
                message=message,
                level=AlertService.normalize_level(notification_data.get("level")),
                suggested_action=notification_data.get("suggested_action", ""),
                source_alert_id=source_alert_id,
                source_metric_type=notification_data.get("source_metric_type", ""),
                payload=notification_data.get("payload") or {},
                metadata={"source": "farm_alerts_tracker_ai"},
            )
        )
    return saved_notifications


def build_tracker_context(*, farm, alerts):
    recent_notifications = serialize_notifications_for_ai(farm=farm, since_days=3, limit=10)
    counts = Counter(
        AlertService.normalize_level(alert.get("level"))
        for alert in alerts
        if alert.get("level")
    )
    structured_context = {
        "farm_uuid": str(farm.farm_uuid),
        "alerts_count": len(alerts),
        "recent_notifications_count": len(recent_notifications),
        "recent_notifications_window_days": 3,
        "recent_notifications_limit": 10,
        "alert_levels": dict(counts),
    }
    return {
        "farm_uuid": str(farm.farm_uuid),
        "alerts": alerts,
        "recent_notifications": recent_notifications,
        "structured_context": structured_context,
    }


def build_tracker_response(*, farm, adapter_payload):
    notifications_payload = adapter_payload.get("notifications") or []
    saved_notifications = save_tracker_notifications(farm_uuid=farm.farm_uuid, notifications=notifications_payload)
    raw_llm_response = adapter_payload.get("raw_llm_response", "")
    if not raw_llm_response:
        raw_llm_response = json.dumps(adapter_payload, ensure_ascii=False)

    return {
        "farm_uuid": str(farm.farm_uuid),
        "service_id": adapter_payload.get("service_id", "farm_alerts"),
        "tracker": adapter_payload.get("tracker") or {},
        "headline": adapter_payload.get("headline", ""),
        "overview": adapter_payload.get("overview", ""),
        "status_level": AlertService.normalize_level(adapter_payload.get("status_level")),
        "notifications": saved_notifications,
        "raw_llm_response": raw_llm_response,
        "structured_context": adapter_payload.get("structured_context") or {},
    }


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
