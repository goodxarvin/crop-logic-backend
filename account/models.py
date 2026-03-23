from django.contrib.auth.models import AbstractUser
from django.contrib.auth.models import UserManager as BaseUserManager
from django.db.models import Q
from django.db import models


class CustomUserManager(BaseUserManager):
    """Manager that allows lookup by username, email, or phone_number."""

    def get_by_natural_key(self, username):
        return self.get(
            Q(username=username) | Q(email=username) | Q(phone_number=username)
        )


class User(AbstractUser):
    phone_number = models.CharField(
        max_length=32,
        unique=True,
        db_index=True,
    )
    email = models.EmailField(
        "email address",
        unique=True,
        db_index=True,
    )

    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = ["email", "phone_number"]

    objects = CustomUserManager()

    class Meta:
        db_table = "users"

    def __str__(self):
        return self.username
