import pytest
from common.enums import ProgressStatus
from courses.models import Progress, Lesson

@pytest.mark.django_db
def test_my_courses_empty(api_client, user_alice):
    api_client.force_authenticate(user=user_alice)
    url = "/api/v1/courses/my/"
    resp = api_client.get(url)
    assert resp.status_code == 200
    assert len(resp.data) == 0

@pytest.mark.django_db
def test_my_courses_progress(api_client, user_alice, course_python, lesson_decorators, lesson_generators):
    # Setup lessons
    lesson_decorators.order = 1
    lesson_decorators.save()
    lesson_generators.order = 2
    lesson_generators.save()
    
    # Alice starts lesson 1 (Incomplete)
    Progress.objects.create(
        user=user_alice, 
        lesson=lesson_decorators, 
        status=ProgressStatus.INCOMPLETE
    )
    
    api_client.force_authenticate(user=user_alice)
    url = "/api/v1/courses/my/"
    resp = api_client.get(url)
    
    assert resp.status_code == 200
    assert len(resp.data) == 1
    data = resp.data[0]
    assert data["slug"] == course_python.slug
    assert data["completion_percentage"] == 0
    assert data["is_completed"] == False

    # Alice completes lesson 1 (1/2 = 50%)
    p = Progress.objects.get(user=user_alice, lesson=lesson_decorators)
    p.status = ProgressStatus.COMPLETED
    p.save()
    
    resp = api_client.get(url)
    assert resp.data[0]["completion_percentage"] == 50
    assert resp.data[0]["is_completed"] == False

    # Alice completes lesson 2 (2/2 = 100%)
    Progress.objects.create(
        user=user_alice,
        lesson=lesson_generators,
        status=ProgressStatus.COMPLETED
    )
    
    resp = api_client.get(url)
    assert resp.data[0]["completion_percentage"] == 100
    assert resp.data[0]["is_completed"] == True
