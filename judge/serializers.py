from rest_framework import serializers
from .models import Language, Problem, Submission


class LanguageSer(serializers.ModelSerializer):
    class Meta:
        model = Language
        fields = ("id", "key", "version")


class ProblemListSer(serializers.ModelSerializer):
    class Meta:
        model = Problem
        fields = ("id", "slug", "title")


class ProblemDetailSer(serializers.ModelSerializer):
    # NEW: send allowed languages (full objects) to the frontend
    allowed_languages = LanguageSer(many=True, read_only=True)

    class Meta:
        model = Problem
        fields = (
            "id",
            "slug",
            "title",
            "statement_md",
            "time_limit_ms",
            "memory_limit_mb",
            "allowed_languages",
        )


class SubmitSer(serializers.Serializer):
    language_id = serializers.UUIDField()
    code = serializers.CharField(min_length=1, max_length=100_000)

    def validate_code(self, value: str) -> str:
        if not value.strip():
            raise serializers.ValidationError("Code cannot be blank.")
        return value


class SubmissionSer(serializers.ModelSerializer):
    problem = ProblemListSer(read_only=True)
    language = LanguageSer(read_only=True)

    class Meta:
        model = Submission
        fields = ("id", "status", "summary", "problem", "language", "created_at")
        read_only_fields = fields
