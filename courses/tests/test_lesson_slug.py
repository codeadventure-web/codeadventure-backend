import pytest
from courses.models import Lesson


@pytest.mark.django_db
def test_lesson_slug_from_order(course_python):
    lesson = Lesson.objects.create(course=course_python, title="My Lesson", order=5)
    # Expecting simple string "05" per new requirement
    assert lesson.slug == "05"


@pytest.mark.django_db
def test_lesson_slug_enforced_from_order(course_python):
    # Even if slug is provided, it should be overwritten by order
    lesson = Lesson.objects.create(
        course=course_python, title="My Lesson", order=5, slug="special-lesson"
    )
    assert lesson.slug == "05"
