from django.db import models
from common.models import UUIDModel, TimeStamped


class Quiz(UUIDModel, TimeStamped):
    lesson = models.OneToOneField(
        "courses.Lesson", on_delete=models.CASCADE, related_name="quiz"
    )


class Question(UUIDModel, TimeStamped):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name="questions")
    text = models.TextField()
    type = models.CharField(
        max_length=20, choices=[("single", "Single"), ("multi", "Multi")]
    )


class Choice(UUIDModel, TimeStamped):
    question = models.ForeignKey(
        Question, on_delete=models.CASCADE, related_name="choices"
    )
    text = models.CharField(max_length=500)
    is_correct = models.BooleanField(default=False)


class QuizAttempt(UUIDModel, TimeStamped):
    user = models.ForeignKey("accounts.User", on_delete=models.CASCADE)
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE)
    score = models.FloatField(default=0.0)
    finished = models.BooleanField(default=False)


class QuizAnswer(UUIDModel, TimeStamped):
    attempt = models.ForeignKey(
        QuizAttempt, on_delete=models.CASCADE, related_name="answers"
    )
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    selected_choice_ids = models.JSONField(default=list)
