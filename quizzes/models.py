from django.db import models
from django.conf import settings
from common.models import UUIDModel, TimeStamped


class Quiz(UUIDModel, TimeStamped):
    lesson = models.OneToOneField(
        "courses.Lesson",
        on_delete=models.CASCADE,
        related_name="quiz"
    )
    title = models.CharField(max_length=255)
    questions = models.JSONField()


class QuizAttempt(UUIDModel, TimeStamped):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    answers = models.JSONField(default=dict)
    score = models.IntegerField(default=0)
    total = models.IntegerField(default=0)
