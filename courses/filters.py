import django_filters
from .models import Course, Lesson


class CharInFilter(django_filters.BaseInFilter, django_filters.CharFilter):
    """
    Custom filter to allow comma-separated values for 'in' lookup.
    e.g., ?tags=python,c-plus-plus
    """

    pass


class CourseFilter(django_filters.FilterSet):
    """
    Custom filterset for the Course model.
    Filters by tags and published status.
    """

    # Filter for tags
    tags = CharInFilter(field_name="tags__slug", lookup_expr="in")

    class Meta:
        model = Course
        fields = [
            "is_published",
            "tags",
        ]


class LessonFilter(django_filters.FilterSet):
    class Meta:
        model = Lesson
        fields = ["course", "type"]
