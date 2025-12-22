from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers
from .models import Course, Lesson, Progress, Tag
from common.enums import LessonType
from judge.models import Problem
from quizzes.serializers import QuizSer
from typing import Any, Dict, Optional


class ProblemLiteSer(serializers.ModelSerializer):
    from judge.serializers import LanguageSer

    allowed_languages = LanguageSer(many=True, read_only=True)

    class Meta:
        model = Problem
        fields = ("slug", "title", "allowed_languages")


class ProgressLiteSer(serializers.ModelSerializer):
    class Meta:
        model = Progress
        fields = ("status",)


class LessonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lesson
        fields = (
            "id",
            "course",
            "title",
            "slug",
            "type",
            "order",
            "problem",
            "quiz",
            "content_md",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "slug", "created_at", "updated_at")
        extra_kwargs = {"course": {"required": False}}

    def validate(self, data):
        # Determine the final type, problem, and quiz after this update
        instance = self.instance
        lesson_type = data.get("type", instance.type if instance else LessonType.JUDGE)

        # If type is JUDGE, quiz must be cleared. If type is QUIZ, problem must be cleared.
        if lesson_type == LessonType.JUDGE:
            if data.get("quiz") or (instance and instance.quiz and "quiz" not in data):
                data["quiz"] = None
            if not data.get("problem") and not (instance and instance.problem):
                raise serializers.ValidationError(
                    {"problem": "Judge lesson must have a problem."}
                )
        elif lesson_type == LessonType.QUIZ:
            if data.get("problem") or (
                instance and instance.problem and "problem" not in data
            ):
                data["problem"] = None
            if not data.get("quiz") and not (instance and instance.quiz):
                raise serializers.ValidationError(
                    {"quiz": "Quiz lesson must have a quiz."}
                )

        return data


class LessonLiteSer(serializers.ModelSerializer):
    progress = serializers.SerializerMethodField()
    problem = ProblemLiteSer(read_only=True)
    quiz = serializers.SerializerMethodField()

    class Meta:
        model = Lesson
        fields = (
            "id",
            "title",
            "slug",
            "type",
            "order",
            "problem",
            "quiz",
            "content_md",
            "progress",
        )

    @extend_schema_field(ProgressLiteSer)
    def get_progress(self, obj):
        progress_map = self.context.get("progress_map", {})
        progress = progress_map.get(obj.id)
        if progress:
            return ProgressLiteSer(progress).data
        return None

    @extend_schema_field(QuizSer)
    def get_quiz(self, obj) -> Optional[Dict[str, Any]]:
        if hasattr(obj, "quiz") and obj.quiz:
            return QuizSer(obj.quiz).data
        return None


class CourseListSer(serializers.ModelSerializer):
    tags = serializers.SlugRelatedField(
        many=True,
        slug_field="name",
        queryset=Tag.objects.all(),
        required=False,
    )

    class Meta:
        model = Course
        fields = ("id", "title", "slug", "is_published", "tags")


class CourseDetailSer(serializers.ModelSerializer):
    lessons = LessonLiteSer(many=True, read_only=True)
    tags = serializers.SlugRelatedField(
        many=True,
        slug_field="name",
        queryset=Tag.objects.all(),
        required=False,
    )

    class Meta:
        model = Course
        fields = (
            "id",
            "title",
            "slug",
            "description",
            "is_published",
            "lessons",
            "tags",
        )


class ProgressSer(serializers.ModelSerializer):
    class Meta:
        model = Progress
        fields = ("id", "lesson", "status")


class MyCourseSerializer(serializers.ModelSerializer):
    completion_percentage = serializers.IntegerField()
    is_completed = serializers.BooleanField()

    class Meta:
        model = Course
        fields = ("id", "title", "slug", "completion_percentage", "is_completed")
