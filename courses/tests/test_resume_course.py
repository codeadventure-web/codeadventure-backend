import pytest
from common.enums import ProgressStatus
from courses.models import Progress, Lesson


@pytest.mark.django_db
def test_resume_not_started(
    api_client, user_alice, course_python, lesson_decorators, lesson_generators
):
    # Ensure order
    lesson_decorators.order = 1
    lesson_decorators.save()
    lesson_generators.order = 2
    lesson_generators.save()

    api_client.force_authenticate(user=user_alice)
    url = f"/api/v1/{course_python.slug}/resume/"
    resp = api_client.get(url)

    assert resp.status_code == 200
    assert resp.data["lesson_slug"] == lesson_decorators.slug


@pytest.mark.django_db
def test_resume_partially_completed(
    api_client, user_alice, course_python, lesson_decorators, lesson_generators
):
    lesson_decorators.order = 1
    lesson_decorators.save()
    lesson_generators.order = 2
    lesson_generators.save()

    # Complete lesson 1
    Progress.objects.create(
        user=user_alice, lesson=lesson_decorators, status=ProgressStatus.COMPLETED
    )

    api_client.force_authenticate(user=user_alice)
    url = f"/api/v1/{course_python.slug}/resume/"
    resp = api_client.get(url)

    assert resp.status_code == 200
    assert resp.data["lesson_slug"] == lesson_generators.slug


@pytest.mark.django_db
def test_resume_all_completed(
    api_client, user_alice, course_python, lesson_decorators, lesson_generators
):
    lesson_decorators.order = 1
    lesson_decorators.save()
    lesson_generators.order = 2
    lesson_generators.save()

    # Complete all
    Progress.objects.create(
        user=user_alice, lesson=lesson_decorators, status=ProgressStatus.COMPLETED
    )
    Progress.objects.create(
        user=user_alice, lesson=lesson_generators, status=ProgressStatus.COMPLETED
    )

    api_client.force_authenticate(user=user_alice)
    url = f"/api/v1/{course_python.slug}/resume/"
    resp = api_client.get(url)

    assert resp.status_code == 200
    # Should return first lesson if all done (restart/review)
    assert resp.data["lesson_slug"] == lesson_decorators.slug


@pytest.mark.django_db
def test_resume_no_lessons(api_client, user_alice, course_python):
    Lesson.objects.filter(course=course_python).delete()

    api_client.force_authenticate(user=user_alice)
    url = f"/api/v1/{course_python.slug}/resume/"
    resp = api_client.get(url)

    assert resp.status_code == 404
