from collections import Counter
from copy import deepcopy
import json
import logging

from django.utils import timezone

from external_api_adapter import request as external_api_request
from farm_hub.models import FarmHub
from notifications.models import FarmNotification
from notifications.services import create_notification_for_farm_uuid, get_recent_notifications_for_farm

from .defaults import EMPTY_ALERT_TIMELINE, EMPTY_ALERT_TRACKER, EMPTY_ANOMALY_CARD, EMPTY_RECOMMENDATIONS
from .models import AnomalyDetection, FarmAlert, FarmAlertTrackerSnapshot, Recommendation


LEVEL_ALIAS_MAP = {
    "danger": "error",
    "critical": "error",
    "warn": "warning",
}

TRACKER_AI_NOTIFICATION_SOURCE = "farm_alerts_tracker_ai"
logger = logging.getLogger("farm_alerts")


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


def serialize_notifications_for_ai(*, farm, since_days=3, limit=5):
    notifications = get_recent_notifications_for_farm(farm=farm, since_days=since_days, limit=limit)
    notifications = [item for item in notifications if item.metadata.get("source") != TRACKER_AI_NOTIFICATION_SOURCE]
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
                metadata={"source": TRACKER_AI_NOTIFICATION_SOURCE},
            )
        )
    return saved_notifications


def build_tracker_context(*, farm):
    recent_notifications = serialize_notifications_for_ai(farm=farm, since_days=3, limit=5)
    payload = {"farm_uuid": str(farm.farm_uuid)}

    if recent_notifications:
        counts = Counter(
            AlertService.normalize_level(notification.get("level"))
            for notification in recent_notifications
            if notification.get("level")
        )
        payload["recent_notifications"] = recent_notifications
        payload["structured_context"] = {
            "farm_uuid": str(farm.farm_uuid),
            "notifications_count": len(recent_notifications),
            "recent_notifications_count": len(recent_notifications),
            "recent_notifications_window_days": 3,
            "recent_notifications_limit": 5,
            "notification_levels": dict(counts),
        }

    return payload


def serialize_alerts_for_ai(*, farm, since=None, limit=50):
    queryset = FarmAlert.objects.filter(farm=farm).order_by("-created_at", "-id")
    if since is not None:
        queryset = queryset.filter(created_at__gt=since)

    alerts = queryset[:limit]
    return [
        {
            "alert_id": alert.external_alert_id,
            "level": alert.color,
            "title": alert.title,
            "message": alert.description,
            "suggested_action": alert.suggested_action,
            "source_metric_type": alert.source_metric_type,
            "timestamp": alert.occurred_at.isoformat() if alert.occurred_at else None,
            "payload": alert.payload,
        }
        for alert in alerts
    ]


def get_tracker_notifications(*, farm, limit=10):
    return list(
        FarmNotification.objects.filter(farm=farm, endpoint="tracker")
        .order_by("-created_at", "-id")[:limit]
    )


def get_tracker_source_updated_at(*, farm):
    latest_alert = FarmAlert.objects.filter(farm=farm).order_by("-created_at", "-id").values_list("created_at", flat=True).first()
    latest_notification = (
        FarmNotification.objects.filter(farm=farm)
        .exclude(metadata__source=TRACKER_AI_NOTIFICATION_SOURCE)
        .order_by("-updated_at", "-id")
        .values_list("updated_at", flat=True)
        .first()
    )
    candidates = [item for item in (latest_alert, latest_notification) if item is not None]
    if not candidates:
        return None
    return max(candidates)


def get_or_create_tracker_snapshot(*, farm):
    snapshot, _ = FarmAlertTrackerSnapshot.objects.get_or_create(farm=farm)
    return snapshot


def update_tracker_snapshot(*, farm, adapter_payload, source_updated_at):
    snapshot = get_or_create_tracker_snapshot(farm=farm)
    notifications_payload = adapter_payload.get("notifications") or []
    save_tracker_notifications(farm_uuid=farm.farm_uuid, notifications=notifications_payload)

    raw_llm_response = adapter_payload.get("raw_llm_response", "")
    if not raw_llm_response:
        raw_llm_response = json.dumps(adapter_payload, ensure_ascii=False)

    snapshot.service_id = adapter_payload.get("service_id", "farm_alerts")
    snapshot.tracker = adapter_payload.get("tracker") or {}
    snapshot.headline = adapter_payload.get("headline", "")
    snapshot.overview = adapter_payload.get("overview", "")
    snapshot.status_level = AlertService.normalize_level(adapter_payload.get("status_level"))
    snapshot.raw_llm_response = raw_llm_response
    snapshot.structured_context = adapter_payload.get("structured_context") or {}
    snapshot.last_ai_synced_at = timezone.now()
    snapshot.last_source_update_at = source_updated_at
    snapshot.save(
        update_fields=[
            "service_id",
            "tracker",
            "headline",
            "overview",
            "status_level",
            "raw_llm_response",
            "structured_context",
            "last_ai_synced_at",
            "last_source_update_at",
            "updated_at",
        ]
    )
    return snapshot


def build_tracker_response_from_snapshot(*, farm):
    snapshot = FarmAlertTrackerSnapshot.objects.filter(farm=farm).first()
    notifications = get_tracker_notifications(farm=farm, limit=10)
    if snapshot is None:
        return {
            "farm_uuid": str(farm.farm_uuid),
            "service_id": "farm_alerts",
            "tracker": {},
            "headline": "",
            "overview": "",
            "status_level": "info",
            "notifications": notifications,
            "raw_llm_response": "",
            "structured_context": {},
        }

    return {
        "farm_uuid": str(farm.farm_uuid),
        "service_id": snapshot.service_id,
        "tracker": snapshot.tracker or {},
        "headline": snapshot.headline,
        "overview": snapshot.overview,
        "status_level": AlertService.normalize_level(snapshot.status_level),
        "notifications": notifications,
        "raw_llm_response": snapshot.raw_llm_response,
        "structured_context": snapshot.structured_context or {},
    }


def sync_farm_tracker_with_ai(*, farm):
    snapshot = FarmAlertTrackerSnapshot.objects.filter(farm=farm).first()
    source_updated_at = get_tracker_source_updated_at(farm=farm)
    if source_updated_at is None:
        logger.info(
            "farm=%s tracker sync proceeding without source data snapshot_exists=%s",
            farm.farm_uuid,
            snapshot is not None,
        )

    if (
        source_updated_at is not None
        and snapshot is not None
        and snapshot.last_source_update_at is not None
        and source_updated_at <= snapshot.last_source_update_at
    ):
        logger.info(
            "farm=%s tracker sync skipped: no changes source_updated_at=%s last_source_update_at=%s",
            farm.farm_uuid,
            source_updated_at,
            snapshot.last_source_update_at,
        )
        return {"farm_uuid": str(farm.farm_uuid), "status": "skipped", "reason": "no_changes"}

    tracker_payload = build_tracker_context(farm=farm)
    logger.info(
        "farm=%s tracker sync sending AI request recent_notifications=%s payload=%s",
        farm.farm_uuid,
        len(tracker_payload.get("recent_notifications", [])),
        tracker_payload,
    )
    adapter_response = external_api_request(
        "ai",
        "/api/farm-alerts/tracker/",
        method="POST",
        payload=tracker_payload,
    )
    if adapter_response.status_code >= 400:
        logger.warning(
            "farm=%s tracker sync failed status_code=%s response=%s",
            farm.farm_uuid,
            adapter_response.status_code,
            adapter_response.data,
        )
        raise ValueError(f"AI tracker sync failed with status {adapter_response.status_code}.")

    adapter_data = adapter_response.data if isinstance(adapter_response.data, dict) else {}
    logger.info(
        "farm=%s tracker sync received AI response status_code=%s response=%s",
        farm.farm_uuid,
        adapter_response.status_code,
        adapter_data,
    )
    payload = adapter_data.get("data")
    if isinstance(payload, dict) and isinstance(payload.get("result"), dict):
        payload = payload["result"]
    elif not isinstance(payload, dict):
        payload = adapter_data.get("result") if isinstance(adapter_data.get("result"), dict) else adapter_data
    logger.info(
        "farm=%s tracker sync normalized AI payload=%s",
        farm.farm_uuid,
        payload,
    )

    update_tracker_snapshot(
        farm=farm,
        adapter_payload=payload or {},
        source_updated_at=source_updated_at,
    )
    logger.info("farm=%s tracker sync completed successfully", farm.farm_uuid)
    return {"farm_uuid": str(farm.farm_uuid), "status": "synced"}


def sync_all_farm_alert_trackers():
    farms = FarmHub.objects.all().order_by("id")
    logger.info("farm alerts sync discovered %s farm(s) to process", farms.count())
    results = []
    for farm in farms:
        results.append(sync_farm_tracker_with_ai(farm=farm))
    return {"processed": len(results), "results": results}
def get_alert_tracker_data(farm=None):
    if farm is None:
        return deepcopy(EMPTY_ALERT_TRACKER)

    alerts = list(FarmAlert.objects.filter(farm=farm, is_active=True)[:20])
    if not alerts:
        return deepcopy(EMPTY_ALERT_TRACKER)

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
        "status": "success",
        "source": "db",
        "warnings": [],
    }


def get_alert_timeline_data(farm=None):
    if farm is None:
        return deepcopy(EMPTY_ALERT_TIMELINE)

    alerts = list(FarmAlert.objects.filter(farm=farm)[:10])
    if not alerts:
        return deepcopy(EMPTY_ALERT_TIMELINE)

    return {
        "alerts": [
            {
                "title": alert.title,
                "description": alert.description,
                "time": alert.created_at.strftime("%Y-%m-%d %H:%M"),
                "color": alert.color,
            }
            for alert in alerts
        ],
        "status": "success",
        "source": "db",
        "warnings": [],
    }


def get_anomaly_detection_data(farm=None):
    if farm is None:
        return deepcopy(EMPTY_ANOMALY_CARD)

    anomalies = list(AnomalyDetection.objects.filter(farm=farm)[:10])
    if not anomalies:
        return deepcopy(EMPTY_ANOMALY_CARD)

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
        ],
        "status": "success",
        "source": "db",
        "warnings": [],
    }


def get_recommendations_list_data(farm=None):
    if farm is None:
        return deepcopy(EMPTY_RECOMMENDATIONS)

    recommendations = list(Recommendation.objects.filter(farm=farm)[:10])
    if not recommendations:
        return deepcopy(EMPTY_RECOMMENDATIONS)

    return {
        "recommendations": [
            {
                "title": recommendation.title,
                "subtitle": recommendation.subtitle,
                "avatarIcon": recommendation.avatar_icon or "tabler-bulb",
                "avatarColor": recommendation.avatar_color or "info",
            }
            for recommendation in recommendations
        ],
        "status": "success",
        "source": "db",
        "warnings": [],
    }
