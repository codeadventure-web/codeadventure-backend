from django.db import models
from django.contrib.auth.models import AbstractUser
from common.models import UUIDModel
from common.enums import UserRole


class User(AbstractUser):
    """
    Custom user model for CodeAdventure.

    We use the built-in fields from AbstractUser (username, email, etc.)
    and add a custom 'role' field.
    """

    # Use the enum for choices and set a default
    role = models.CharField(
        max_length=10, choices=UserRole.choices, default=UserRole.USER
    )

    def __str__(self):
        return self.username


class Profile(UUIDModel):
    """
    User profile model.

    This inherits its UUID 'id' field from common.models.UUIDModel.
    It's linked one-to-one with the User model.
    """

    # The 'id' field is inherited from UUIDModel

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    avatar = models.URLField(max_length=200, blank=True, null=True)
    bio = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"
