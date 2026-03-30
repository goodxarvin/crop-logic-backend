from django.apps import AppConfig


class CropZoningConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "crop_zoning"
    verbose_name = "Crop Zoning"

    def ready(self):
        from . import tasks  # noqa: F401
