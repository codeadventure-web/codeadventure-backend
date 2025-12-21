from django.db import models
from django.utils.text import slugify
from common.models import UUIDModel, TimeStamped
from common.enums import ProgressStatus


class Tag(UUIDModel, TimeStamped):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Course(UUIDModel, TimeStamped):
    class Meta:
        ordering = ["title"]

    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    is_published = models.BooleanField(default=False)

    # Add ManyToManyField to link Courses and Tags
    tags = models.ManyToManyField(Tag, blank=True, related_name="courses")

    def __str__(self):
        return self.title


class Lesson(UUIDModel, TimeStamped):
    class Meta:
        ordering = ["order", "created_at"]

    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="lessons")
    title = models.CharField(max_length=200)
    order = models.PositiveIntegerField(default=0)
    content_md = models.TextField(blank=True)
    problem = models.ForeignKey(
        "judge.Problem", null=True, blank=True, on_delete=models.SET_NULL
    )


class Progress(UUIDModel, TimeStamped):
    user = models.ForeignKey("accounts.User", on_delete=models.CASCADE)
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE)
    status = models.CharField(
        max_length=20,
        choices=ProgressStatus.choices,
        default=ProgressStatus.INCOMPLETE,
    )
    score = models.FloatField(null=True, blank=True)

    class Meta:
        unique_together = ("user", "lesson")
