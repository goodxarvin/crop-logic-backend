import uuid as uuid_lib

from django.db import models


class SubscriptionPlan(models.Model):
    uuid = models.UUIDField(default=uuid_lib.uuid4, unique=True, editable=False, db_index=True)
    code = models.SlugField(max_length=64, unique=True, db_index=True)
    name = models.CharField(max_length=255, unique=True, db_index=True)
    description = models.TextField(blank=True, default="")
    metadata = models.JSONField(default=dict, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "subscription_plans"
        ordering = ["name"]

    def __str__(self):
        return self.name


class AccessFeature(models.Model):
    PAGE = "page"
    ACTION = "action"
    WIDGET = "widget"
    SECTION = "section"
    FEATURE_TYPES = [
        (PAGE, "Page"),
        (ACTION, "Action"),
        (WIDGET, "Widget"),
        (SECTION, "Section"),
    ]

    uuid = models.UUIDField(default=uuid_lib.uuid4, unique=True, editable=False, db_index=True)
    code = models.SlugField(max_length=128, unique=True, db_index=True)
    name = models.CharField(max_length=255)
    feature_type = models.CharField(max_length=32, choices=FEATURE_TYPES, default=PAGE)
    description = models.TextField(blank=True, default="")
    default_enabled = models.BooleanField(default=False)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "access_features"
        ordering = ["feature_type", "code"]

    def __str__(self):
        return self.code


class AccessRule(models.Model):
    ALLOW = "allow"
    DENY = "deny"
    EFFECTS = [
        (ALLOW, "Allow"),
        (DENY, "Deny"),
    ]

    uuid = models.UUIDField(default=uuid_lib.uuid4, unique=True, editable=False, db_index=True)
    code = models.SlugField(max_length=128, unique=True, db_index=True)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, default="")
    effect = models.CharField(max_length=16, choices=EFFECTS, default=ALLOW)
    priority = models.PositiveIntegerField(default=100)
    is_active = models.BooleanField(default=True)
    metadata = models.JSONField(default=dict, blank=True)
    features = models.ManyToManyField(AccessFeature, related_name="rules", blank=True)
    subscription_plans = models.ManyToManyField(SubscriptionPlan, related_name="access_rules", blank=True)
    farm_types = models.ManyToManyField("farm_hub.FarmType", related_name="access_rules", blank=True)
    products = models.ManyToManyField("farm_hub.Product", related_name="access_rules", blank=True)
    sensor_catalogs = models.ManyToManyField("sensor_catalog.SensorCatalog", related_name="access_rules", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "access_rules"
        ordering = ["priority", "code"]

    def __str__(self):
        return self.code


class FarmAccessProfile(models.Model):
    farm = models.OneToOneField(
        "farm_hub.FarmHub",
        to_field="farm_uuid",
        db_column="farm_uuid",
        on_delete=models.CASCADE,
        related_name="access_profile",
        primary_key=True,
    )
    cached_features = models.JSONField(default=dict, blank=True)
    cached_groups = models.JSONField(default=dict, blank=True)
    matched_rules = models.JSONField(default=list, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    last_resolved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "farm_access_profiles"

    def __str__(self):
        return str(self.farm_id)

