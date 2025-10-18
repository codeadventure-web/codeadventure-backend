import uuid
from django.db import models


class UUIDModel(models.Model):
    """
    Abstract model that uses a UUID primary key.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    class Meta:
        abstract = True


class TimeStamped(models.Model):
    """
    Abstract model that tracks created/updated times.
    """

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
