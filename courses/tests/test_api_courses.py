import pytest
from common.enums import ProgressStatus
from courses.models import Progress


@pytest.mark.django_db
def test_course_list_filter(api_client, course_python, tag_python):
    url = "/api/courses/"

    # Test filter by tag
    resp = api_client.get(f"{url}?tags={tag_python.slug}")
    assert resp.status_code == 200
    # assert len(resp.data) == 1
    assert len(resp.data["results"]) == 1
    assert resp.data[0]["title"] == course_python.title


@pytest.mark.django_db
def test_course_detail_structure(api_client, course_python, lesson_decorators):
    url = f"/api/courses/{course_python.slug}/"
    resp = api_client.get(url)

    assert resp.status_code == 200
    assert "lessons" in resp.data
    assert len(resp.data["lessons"]) > 0


# --- ISOLATION TESTS ---


@pytest.mark.django_db
def test_authenticated_user_sees_own_progress(
    api_client, user_alice, course_python, lesson_decorators
):
    # Alice completes the lesson
    Progress.objects.create(
        user=user_alice,
        lesson=lesson_decorators,
        status=ProgressStatus.COMPLETED,
        score=100,
    )

    # Login as Alice
    api_client.force_authenticate(user=user_alice)

    url = f"/api/courses/{course_python.slug}/"
    resp = api_client.get(url)

    lessons = resp.data["lessons"]
    target_lesson = next(
        lesson for lesson in lessons if lesson["id"] == str(lesson_decorators.id)
    )

    assert target_lesson["progress"] is not None
    assert target_lesson["progress"]["status"] == ProgressStatus.COMPLETED
    assert target_lesson["progress"]["score"] == 100.0


@pytest.mark.django_db
def test_data_isolation_between_users(
    api_client, user_alice, user_bob, course_python, lesson_decorators
):
    # Alice completes the lesson
    Progress.objects.create(
        user=user_alice, lesson=lesson_decorators, status=ProgressStatus.COMPLETED
    )

    # Login as Bob (Who has NOT started)
    api_client.force_authenticate(user=user_bob)

    url = f"/api/courses/{course_python.slug}/"
    resp = api_client.get(url)

    lessons = resp.data["lessons"]
    target_lesson = next(
        lesson for lesson in lessons if lesson["id"] == str(lesson_decorators.id)
    )

    # Bob should see None, despite Alice having a record
    assert target_lesson["progress"] is None
