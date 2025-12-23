from django.db import models
from common.models import UUIDModel, TimeStamped


class Quiz(UUIDModel, TimeStamped):
    title = models.CharField(max_length=200, default="Untitled Quiz")

    def __str__(self):
        return self.title


class Question(UUIDModel, TimeStamped):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name="questions")
    text = models.TextField()


class Choice(UUIDModel, TimeStamped):
    question = models.ForeignKey(
        Question, on_delete=models.CASCADE, related_name="choices"
    )
    text = models.CharField(max_length=500)
    is_answer = models.BooleanField(default=False)
