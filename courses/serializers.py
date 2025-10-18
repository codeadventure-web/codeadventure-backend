from rest_framework import serializers
from .models import Course, Section, Lesson, Enrollment, Progress


class LessonLiteSer(serializers.ModelSerializer):
    class Meta:
        model = Lesson
        fields = ("id", "title", "order", "problem", "content_md")


class SectionSer(serializers.ModelSerializer):
    lessons = LessonLiteSer(many=True, read_only=True)

    class Meta:
        model = Section
        fields = ("id", "title", "order", "lessons")


class CourseListSer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = ("id", "title", "slug", "is_published")


class CourseDetailSer(serializers.ModelSerializer):
    sections = SectionSer(many=True, read_only=True)

    class Meta:
        model = Course
        fields = ("id", "title", "slug", "description", "is_published", "sections")


class EnrollmentSer(serializers.ModelSerializer):
    class Meta:
        model = Enrollment
        fields = ("id", "user", "course", "active")
        read_only_fields = ("user", "active")


class ProgressSer(serializers.ModelSerializer):
    class Meta:
        model = Progress
        fields = ("id", "lesson", "status", "score")
