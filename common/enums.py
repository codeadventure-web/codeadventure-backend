from django.db import models


class LessonType(models.TextChoices):
    JUDGE = "judge", "Judge Problem"
    QUIZ = "quiz", "Quiz"


class SubmissionStatus(models.TextChoices):
    """
    Statuses for the judge.Submission model.
    """

    QUEUED = "queued", "Queued"
    RUNNING = "running", "Running"
    ACCEPTED = "ac", "Accepted"
    WRONG_ANSWER = "wa", "Wrong Answer"
    TIME_LIMIT = "tle", "Time Limit"
    MEMORY_LIMIT = "mle", "Memory Limit"
    RUNTIME_ERROR = "re", "Runtime Error"
    COMPILE_ERROR = "ce", "Compile Error"


class ProgressStatus(models.TextChoices):
    """
    Statuses for lesson progress.
    """

    INCOMPLETE = "incomplete", "Incomplete"
    COMPLETED = "completed", "Completed"


class QuestionType(models.TextChoices):
    """
    Type of quiz question.
    """

    SINGLE = "single", "Single"
    MULTI = "multi", "Multi"
