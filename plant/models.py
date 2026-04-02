from django.db import models


class Plant(models.Model):
    name = models.CharField(max_length=255, unique=True, db_index=True, help_text="نام گیاه")
    light = models.CharField(max_length=255, blank=True, help_text="نور مورد نیاز")
    watering = models.CharField(max_length=255, blank=True, help_text="آبیاری")
    soil = models.CharField(max_length=255, blank=True, help_text="خاک مناسب")
    temperature = models.CharField(max_length=255, blank=True, help_text="دمای مناسب")
    planting_season = models.CharField(max_length=255, blank=True, help_text="فصل کاشت")
    harvest_time = models.CharField(max_length=255, blank=True, help_text="زمان برداشت")
    spacing = models.CharField(max_length=255, blank=True, help_text="فاصله کاشت")
    fertilizer = models.CharField(max_length=255, blank=True, help_text="کود مناسب")
    health_profile = models.JSONField(
        blank=True,
        default=dict,
        help_text=(
            "پروفایل سلامت گیاه برای KPIها. ساختار نمونه: "
            '{"moisture": {"ideal_value": 65, "min_range": 45, "max_range": 75, "weight": 0.4}}'
        ),
    )
    irrigation_profile = models.JSONField(
        blank=True,
        default=dict,
        help_text=(
            "پروفایل آبیاری گیاه برای محاسبات ETc. "
            '{"kc_initial": 0.6, "kc_mid": 1.15, "kc_end": 0.8, '
            '"growth_stage_duration": {"initial": 20, "mid": 30, "late": 25}}'
        ),
    )
    growth_profile = models.JSONField(
        blank=True,
        default=dict,
        help_text=(
            "پروفایل رشد گیاه برای مدل GDD. "
            '{"base_temperature": 10, "required_gdd_for_maturity": 1200, '
            '"stage_thresholds": {"flowering": 500, "fruiting": 850}, "current_cumulative_gdd": 320}'
        ),
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "گیاه"
        verbose_name_plural = "گیاهان"
        ordering = ["name"]

    def __str__(self):
        return self.name
