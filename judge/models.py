from django.db import models
from common.models import UUIDModel, TimeStamped


class Language(UUIDModel):
    key = models.CharField(max_length=20, unique=True)  # "python", "cpp", "java"
    version = models.CharField(max_length=50)


class Problem(UUIDModel, TimeStamped):
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    statement_md = models.TextField()
    time_limit_ms = models.IntegerField(default=2000)
    memory_limit_mb = models.IntegerField(default=256)


class TestCase(UUIDModel, TimeStamped):
    problem = models.ForeignKey(
        Problem, on_delete=models.CASCADE, related_name="testcases"
    )
    input_data = models.TextField()
    expected_output = models.TextField()
    hidden = models.BooleanField(default=True)


class Submission(UUIDModel, TimeStamped):
    user = models.ForeignKey("accounts.User", on_delete=models.CASCADE)
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE)
    language = models.ForeignKey(Language, on_delete=models.PROTECT)
    code = models.TextField()
    status = models.CharField(
        max_length=20,
        default="queued",
        choices=[
            ("queued", "Queued"),
            ("running", "Running"),
            ("ac", "Accepted"),
            ("wa", "Wrong Answer"),
            ("tle", "Time Limit"),
            ("re", "Runtime Error"),
            ("ce", "Compile Error"),
        ],
    )
    summary = models.JSONField(default=dict)
