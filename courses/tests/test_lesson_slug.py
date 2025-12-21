import pytest
from courses.models import Lesson


@pytest.mark.django_db
def test_lesson_slug_from_order(course_python):
    lesson = Lesson.objects.create(course=course_python, title="My Lesson", order=5)
    # Expecting padded string "05"
    assert lesson.slug == "05"


@pytest.mark.django_db
def test_lesson_slug_manual_override(course_python):
    lesson = Lesson.objects.create(
        course=course_python, title="My Lesson", order=5, slug="special-lesson"
    )
    assert lesson.slug == "special-lesson"
