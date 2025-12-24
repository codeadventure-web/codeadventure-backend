import pytest
from courses.models import Lesson
from judge.models import Problem, Language


@pytest.fixture
def lang_python(db):
    return Language.objects.create(key="python")


@pytest.fixture
def problem_sum(db, lang_python):
    p = Problem.objects.create(title="Sum Two", slug="sum-two", time_limit_ms=1000)
    p.allowed_languages.add(lang_python)
    return p


@pytest.fixture
def lesson_with_problem(db, course_python, problem_sum):
    return Lesson.objects.create(
        course=course_python, title="Lesson with Problem", order=10, problem=problem_sum
    )


@pytest.mark.django_db
def test_lesson_detail_includes_ui_fields(
    api_client, course_python, lesson_with_problem, problem_sum, lang_python
):
    # Setup
    lesson_with_problem.content_md = "# Lesson Theory\nCalculate sum of a and b"
    lesson_with_problem.save()

    url = f"/api/v1/{course_python.slug}/{lesson_with_problem.slug}/"
    resp = api_client.get(url)

    assert resp.status_code == 200
    data = resp.data

    # Check top-level lesson data (Theory)
    assert "content_md" in data
    assert "# Lesson Theory" in data["content_md"]
    assert "Calculate sum" in data["content_md"]

    # Check integrated problem data
    assert "problem" in data
    assert data["problem"]["slug"] == problem_sum.slug
    assert "statement_md" not in data["problem"]

    # Check languages for the editor dropdown
    assert "allowed_languages" in data["problem"]
    assert len(data["problem"]["allowed_languages"]) > 0
    assert data["problem"]["allowed_languages"][0]["key"] == "python"
