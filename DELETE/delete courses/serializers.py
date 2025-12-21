from rest_framework import serializers
from .models import Course, Lesson, Progress, Tag


class ProgressLiteSer(serializers.ModelSerializer):
    """
    A simple serializer to show just the lesson's progress status and score.
    """

    class Meta:
        model = Progress
        fields = ("status", "score")


class LessonLiteSer(serializers.ModelSerializer):
    progress = serializers.SerializerMethodField()

    class Meta:
        model = Lesson
        fields = ("id", "title", "order", "problem", "content_md", "progress")

    def get_progress(self, obj: Lesson):
        """
        Gets the user's progress for this specific lesson.

        We look for a 'progress_map' that the viewset will provide
        in the serializer's context.
        """
        progress_map = self.context.get("progress_map", {})
        progress = progress_map.get(obj.id)

        if progress:
            return ProgressLiteSer(progress).data
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
        fields = ("id", "lesson", "status", "score")
