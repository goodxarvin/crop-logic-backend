import json
import uuid
from datetime import datetime, timezone

from django.conf import settings
from redis import Redis


def get_notifications_redis_client():
    redis_url = getattr(settings, "NOTIFICATION_REDIS_URL", None) or _default_redis_url()
    return Redis.from_url(redis_url, decode_responses=True)


def publish_notification(channel, title, message, *, level="info", metadata=None, event="notification"):
    payload = {
        "id": str(uuid.uuid4()),
        "event": event,
        "title": title,
        "message": message,
        "level": level,
        "metadata": metadata or {},
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    redis_client = get_notifications_redis_client()
    redis_client.publish(channel, json.dumps(payload))
    return payload


def _default_redis_url():
    broker_url = getattr(settings, "CELERY_BROKER_URL", "")
    if isinstance(broker_url, str) and broker_url.startswith("redis://"):
        return broker_url
    return "redis://127.0.0.1:6379/1"
