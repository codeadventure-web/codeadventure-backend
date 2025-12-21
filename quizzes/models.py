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
    is_correct = models.BooleanField(default=False)


class QuizAttempt(UUIDModel, TimeStamped):
    user = models.ForeignKey("accounts.User", on_delete=models.CASCADE)
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE)
    is_passed = models.BooleanField(default=False)
    finished = models.BooleanField(default=False)


class QuizAnswer(UUIDModel, TimeStamped):
    attempt = models.ForeignKey(
        QuizAttempt, on_delete=models.CASCADE, related_name="answers"
    )
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    selected_choice_ids = models.JSONField(default=list)
