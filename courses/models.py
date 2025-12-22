from django.db import models
from django.utils.text import slugify
from django.core.exceptions import ValidationError
from common.models import UUIDModel, TimeStamped
from common.enums import ProgressStatus, LessonType


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
        unique_together = ("course", "slug")

    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="lessons")
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, blank=True, null=True, default=None)
    order = models.PositiveIntegerField(default=0)
    content_md = models.TextField(blank=True)

    # New fields for lesson type
    type = models.CharField(
        max_length=10, choices=LessonType.choices, default=LessonType.JUDGE
    )
    problem = models.ForeignKey(
        "judge.Problem", null=True, blank=True, on_delete=models.SET_NULL
    )
    quiz = models.ForeignKey(
        "quizzes.Quiz",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="lesson_for_quiz",
    )

    def get_next_lesson(self):
        return (
            Lesson.objects.filter(course=self.course, order__gt=self.order)
            .order_by("order")
            .first()
        )

    def save(self, *args, **kwargs):
        if self._state.adding and int(self.order or 0) == 0:
            max_order = Lesson.objects.filter(course=self.course).aggregate(
                models.Max("order")
            )["order__max"]
            self.order = (max_order or 0) + 1

        # Always update slug based on order
        self.slug = f"{int(self.order):02d}"
        super().save(*args, **kwargs)

    def clean(self):
        # Ensure that only one of problem or quiz is set, matching the type
        if self.type == LessonType.JUDGE:
            if not self.problem:
                raise ValidationError("Judge lesson must have a problem.")
            if self.quiz:
                raise ValidationError("Judge lesson cannot have a quiz.")
        elif self.type == LessonType.QUIZ:
            if not self.quiz:
                raise ValidationError("Quiz lesson must have a quiz.")
            if self.problem:
                raise ValidationError("Quiz lesson cannot have a problem.")


class Progress(UUIDModel, TimeStamped):
    user = models.ForeignKey("accounts.User", on_delete=models.CASCADE)
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE)
    status = models.CharField(
        max_length=20,
        choices=ProgressStatus.choices,
        default=ProgressStatus.INCOMPLETE,
    )

    class Meta:
        unique_together = ("user", "lesson")
