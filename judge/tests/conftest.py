import pytest
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from judge.models import Language, Problem
from courses.models import Course, Lesson

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user_student(db):
    return User.objects.create_user(username="student", password="password")


@pytest.fixture
def lang_python(db):
    return Language.objects.create(key="python")


@pytest.fixture
def problem_sum(db, lang_python):
    p = Problem.objects.create(title="Sum Two", slug="sum-two", time_limit_ms=1000)
    p.allowed_languages.add(lang_python)
    return p


@pytest.fixture
def course_python(db):
    return Course.objects.create(title="Python Course", slug="python-course")


@pytest.fixture
def lesson_with_problem(db, course_python, problem_sum):
    return Lesson.objects.create(
        course=course_python, title="Lesson 1", order=1, problem=problem_sum
    )
