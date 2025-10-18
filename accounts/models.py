from django.contrib.auth.models import AbstractUser
from django.db import models
from common.models import UUIDModel, TimeStamped


class User(AbstractUser, UUIDModel):
    role = models.CharField(
        max_length=20, default="user", choices=[("admin", "Admin"), ("user", "User")]
    )


class Profile(UUIDModel, TimeStamped):
    user = models.OneToOneField(
        "accounts.User", on_delete=models.CASCADE, related_name="profile"
    )
    avatar = models.URLField(blank=True)
    bio = models.TextField(blank=True)
