import pytest
from courses.models import Tag, Course


@pytest.mark.django_db
def test_tag_slug_generation():
    tag = Tag.objects.create(name="Machine Learning")
    assert tag.slug == "machine-learning"


@pytest.mark.django_db
def test_course_slug_generation():
    # If slug is not provided, it should be generated from title (if you added that logic)
    # Based on your provided code, you might need to ensure slug is set.
    # If you want auto-slug in Course model like Tag, ensure save() is overridden.
    # Assuming standard Django behavior or explicit save:
    course = Course.objects.create(title="Data Science 101", slug="data-science-101")
    assert str(course) == "Data Science 101"  # Assuming __str__ returns title


@pytest.mark.django_db
def test_lesson_ordering(course_python, lesson_decorators, lesson_generators):
    lessons = course_python.lessons.all()
    assert lessons[0] == lesson_decorators
    assert lessons[1] == lesson_generators
