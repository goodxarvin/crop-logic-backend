from django.db import models


class FarmerPriority(models.TextChoices):
    HIGH = "زیاد", "High"
    MEDIUM = "متوسط", "Medium"
    LOW = "کم", "Low"


class FarmerTag(models.TextChoices):
    IRRIGATION = "آبیاری", "آبیاری"
    PEST = "آفت", "آفت"
    URGENT = "فوری", "فوری"
    DAILY = "روزانه", "روزانه"
    MANUAL = "ثبت دستی", "ثبت دستی"
    VISIT = "بازدید", "بازدید"
    FERTILIZATION = "کوددهی", "کوددهی"
    SPRAYING = "سمپاشی", "سمپاشی"
    HARVEST = "برداشت", "برداشت"


FARMER_TAG_CHOICES = [(tag.value, tag.label) for tag in FarmerTag]
FARMER_TAG_VALUES = {tag.value for tag in FarmerTag}
FARMER_TAG_ITEMS = [
    {
        "id": f"tag_{tag.name.lower()}",
        "label": tag.label,
        "value": tag.value,
    }
    for tag in FarmerTag
]


PRIORITY_INPUT_MAP = {
    "high": FarmerPriority.HIGH,
    "medium": FarmerPriority.MEDIUM,
    "low": FarmerPriority.LOW,
    FarmerPriority.HIGH.value: FarmerPriority.HIGH,
    FarmerPriority.MEDIUM.value: FarmerPriority.MEDIUM,
    FarmerPriority.LOW.value: FarmerPriority.LOW,
}
