from django.apps import AppConfig


class FertilizationConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "fertilization"
    label = "fertilization_recommendation"
    verbose_name = "Fertilization Recommendation & Plan Parser"
