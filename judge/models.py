from django.db import models
from common.models import UUIDModel, TimeStamped


class Language(UUIDModel):
    key = models.CharField(max_length=20, unique=True)  # "python", "cpp", "java"
    version = models.CharField(max_length=50)

    class Meta:
        ordering = ("key",)

    def __str__(self) -> str:
        return f"{self.key} ({self.version})"


class Problem(UUIDModel, TimeStamped):
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    statement_md = models.TextField()
    time_limit_ms = models.IntegerField(default=2000)
    memory_limit_mb = models.IntegerField(default=256)

    # NEW: per-problem language restriction
    # If this is empty => all languages are allowed (for old / generic problems)
    allowed_languages = models.ManyToManyField(
        Language,
        related_name="problems",
        blank=True,
        help_text="If empty, all languages are allowed for this problem.",
    )

    class Meta:
        ordering = ("title",)

    def __str__(self) -> str:
        return self.title


class TestCase(UUIDModel, TimeStamped):
    problem = models.ForeignKey(
        Problem, on_delete=models.CASCADE, related_name="testcases"
    )
    input_data = models.TextField()
    expected_output = models.TextField()
    hidden = models.BooleanField(default=True)

    class Meta:
        ordering = ("created_at",)

    def __str__(self) -> str:
        visibility = "hidden" if self.hidden else "public"
        return f"TestCase({self.problem.slug}, {visibility})"


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

    class Meta:
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=("user", "problem")),
            models.Index(fields=("problem", "status")),
        ]

    def __str__(self) -> str:
        return (
            f"Submission({self.id}) {self.user} -> {self.problem.slug} [{self.status}]"
        )
