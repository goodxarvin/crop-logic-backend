import uuid

from django.conf import settings
from django.db import models

from farm_hub.models import FarmHub


class Conversation(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False, db_index=True)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="farm_ai_conversations",
    )
    farm = models.ForeignKey(
        FarmHub,
        on_delete=models.CASCADE,
        related_name="ai_conversations",
        null=True,
        blank=True,
    )
    title = models.CharField(max_length=255, blank=True, default="")
    farm_context = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "farm_ai_conversations"
        ordering = ["-updated_at", "-created_at"]

    def __str__(self):
        return self.title or f"Conversation {self.uuid}"


class Message(models.Model):
    ROLE_USER = "user"
    ROLE_ASSISTANT = "assistant"
    ROLE_CHOICES = (
        (ROLE_USER, "User"),
        (ROLE_ASSISTANT, "Assistant"),
    )

    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False, db_index=True)
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name="messages",
    )
    farm = models.ForeignKey(
        FarmHub,
        on_delete=models.CASCADE,
        related_name="ai_messages",
        null=True,
        blank=True,
    )
    role = models.CharField(max_length=32, choices=ROLE_CHOICES)
    content = models.TextField(blank=True, default="")
    images = models.JSONField(default=list, blank=True)
    raw_response = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "farm_ai_messages"
        ordering = ["created_at", "id"]

    def __str__(self):
        return f"{self.role}: {self.uuid}"
