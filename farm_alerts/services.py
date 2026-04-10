from farm_hub.models import FarmHub
from notifications.models import FarmNotification

from .models import FarmAlert


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
