import pytest
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from courses.models import Course, Lesson, Tag
from judge.models import Problem, Language
from quizzes.models import Quiz

User = get_user_model()


@pytest.fixture
def language_python(db):
    return Language.objects.create(key="python", version="3.13")


@pytest.fixture
def problem_python(db, language_python):
    p = Problem.objects.create(
        title="Sum of Two Numbers",
        slug="sum-of-two",
    )
    p.allowed_languages.add(language_python)
    return p


@pytest.fixture
def quiz_python(db):
    return Quiz.objects.create(title="Python Basics Quiz")


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user_alice(db):
    return User.objects.create_user(
        username="alice", email="alice@test.com", password="password123"
    )


@pytest.fixture
def user_bob(db):
    return User.objects.create_user(
        username="bob", email="bob@test.com", password="password123"
    )


@pytest.fixture
def user_teacher(db):
    return User.objects.create_user(
        username="teacher",
        email="teacher@test.com",
        password="password123",
        is_staff=True,
    )


@pytest.fixture
def tag_python(db):
    return Tag.objects.create(name="Python")


@pytest.fixture
def course_python(db, tag_python):
    course = Course.objects.create(
        title="Advanced Python",
        slug="advanced-python",
        description="Deep dive into Python",
        is_published=True,
    )
    course.tags.add(tag_python)
    return course


@pytest.fixture
def lesson_decorators(db, course_python, problem_python):
    return Lesson.objects.create(
        course=course_python,
        title="Intro to Decorators",
        order=1,
        content_md="# Decorators",
        problem=problem_python,
    )


@pytest.fixture
def lesson_generators(db, course_python):
    return Lesson.objects.create(
        course=course_python, title="Generators", order=2, content_md="# Generators"
    )
