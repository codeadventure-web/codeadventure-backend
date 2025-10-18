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
    class Meta:
        model = Problem
        fields = (
            "id",
            "slug",
            "title",
            "statement_md",
            "time_limit_ms",
            "memory_limit_mb",
        )


class SubmitSer(serializers.Serializer):
    language_id = serializers.UUIDField()
    code = serializers.CharField()


class SubmissionSer(serializers.ModelSerializer):
    class Meta:
        model = Submission
        fields = ("id", "status", "summary", "problem", "language", "created_at")
