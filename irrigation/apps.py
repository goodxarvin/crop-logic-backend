from django.apps import AppConfig


class IrrigationConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "irrigation"
    label = "irrigation_recommendation"
    verbose_name = "Irrigation Recommendation & Plan Parser"
