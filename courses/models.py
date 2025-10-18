from django.db import models
from common.models import UUIDModel, TimeStamped


class Course(UUIDModel, TimeStamped):
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    is_published = models.BooleanField(default=False)


class Section(UUIDModel, TimeStamped):
    course = models.ForeignKey(
        Course, on_delete=models.CASCADE, related_name="sections"
    )
    title = models.CharField(max_length=200)
    order = models.PositiveIntegerField(default=0)


class Lesson(UUIDModel, TimeStamped):
    section = models.ForeignKey(
        Section, on_delete=models.CASCADE, related_name="lessons"
    )
    title = models.CharField(max_length=200)
    order = models.PositiveIntegerField(default=0)
    content_md = models.TextField(blank=True)
    problem = models.ForeignKey(
        "judge.Problem", null=True, blank=True, on_delete=models.SET_NULL
    )


class Enrollment(UUIDModel, TimeStamped):
    user = models.ForeignKey("accounts.User", on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    active = models.BooleanField(default=True)

    class Meta:
        unique_together = ("user", "course")


class Progress(UUIDModel, TimeStamped):
    user = models.ForeignKey("accounts.User", on_delete=models.CASCADE)
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE)
    status = models.CharField(
        max_length=20,
        default="incomplete",
        choices=[("incomplete", "Incomplete"), ("completed", "Completed")],
    )
    score = models.FloatField(null=True, blank=True)

    class Meta:
        unique_together = ("user", "lesson")
