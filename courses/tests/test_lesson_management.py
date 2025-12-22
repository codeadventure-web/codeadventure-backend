import pytest
from common.enums import LessonType


@pytest.mark.django_db
def test_create_lesson_as_teacher(
    api_client, user_teacher, course_python, problem_python
):
    api_client.force_authenticate(user=user_teacher)
    # POST directly to the course slug URL
    url = f"/api/v1/{course_python.slug}/"
    data = {
        "title": "New Lesson",
        "type": LessonType.JUDGE,
        "problem": str(problem_python.id),
        "order": 10,
        "content_md": "Some content",
    }
    resp = api_client.post(url, data)
    assert resp.status_code == 201
    assert resp.data["title"] == "New Lesson"
    assert resp.data["slug"] == "10"


@pytest.mark.django_db
def test_create_lesson_validation_error(api_client, user_teacher, course_python):
    api_client.force_authenticate(user=user_teacher)
    url = f"/api/v1/{course_python.slug}/"

    # JUDGE without problem should fail validation
    data = {
        "title": "Bad Lesson",
        "type": LessonType.JUDGE,
    }
    resp = api_client.post(url, data)
    assert resp.status_code == 400
    assert "problem" in resp.data
    assert "Judge lesson must have a problem." in str(resp.data["problem"])


@pytest.mark.django_db
def test_create_lesson_as_student_fails(api_client, user_alice, course_python):
    api_client.force_authenticate(user=user_alice)
    url = f"/api/v1/{course_python.slug}/"
    data = {
        "title": "New Lesson",
    }
    resp = api_client.post(url, data)
    assert resp.status_code == 403


@pytest.mark.django_db
def test_update_lesson(api_client, user_teacher, lesson_decorators, course_python):
    api_client.force_authenticate(user=user_teacher)
    # PATCH to /course-slug/lesson-slug/
    url = f"/api/v1/{course_python.slug}/{lesson_decorators.slug}/"
    data = {"title": "Updated Title"}
    resp = api_client.patch(url, data)
    assert resp.status_code == 200
    assert resp.data["title"] == "Updated Title"


@pytest.mark.django_db
def test_delete_lesson(api_client, user_teacher, lesson_decorators, course_python):
    api_client.force_authenticate(user=user_teacher)
    # Delete via slug-based URL: /course/lesson/
    url = f"/api/v1/{course_python.slug}/{lesson_decorators.slug}/"
    resp = api_client.delete(url)
    assert resp.status_code == 204


@pytest.mark.django_db
def test_switch_lesson_type_clears_other_field(
    api_client, user_teacher, lesson_decorators, course_python, quiz_python
):
    api_client.force_authenticate(user=user_teacher)
    url = f"/api/v1/{course_python.slug}/{lesson_decorators.slug}/"

    # lesson_decorators is JUDGE by default in conftest. Verify it has a problem.
    assert lesson_decorators.type == LessonType.JUDGE
    assert lesson_decorators.problem is not None
    assert lesson_decorators.quiz is None

    # Switch to QUIZ
    data = {"type": LessonType.QUIZ, "quiz": str(quiz_python.id)}
    resp = api_client.patch(url, data)
    assert resp.status_code == 200
    assert resp.data["type"] == LessonType.QUIZ
    assert str(resp.data["quiz"]) == str(quiz_python.id)
    assert resp.data["problem"] is None

    # Verify in DB
    lesson_decorators.refresh_from_db()
    assert lesson_decorators.type == LessonType.QUIZ
    assert lesson_decorators.quiz == quiz_python
    assert lesson_decorators.problem is None
