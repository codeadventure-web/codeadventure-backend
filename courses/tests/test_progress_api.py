import pytest
from common.enums import ProgressStatus
from courses.models import Progress

@pytest.mark.django_db
def test_manual_complete_lesson(api_client, user_alice, lesson_decorators):
    api_client.force_authenticate(user=user_alice)
    
    url = f"/api/v1/lessons/{lesson_decorators.id}/complete/"
    response = api_client.patch(url)
    
    assert response.status_code == 200
    assert response.data["status"] == ProgressStatus.COMPLETED
    
    # Verify DB
    progress = Progress.objects.get(user=user_alice, lesson=lesson_decorators)
    assert progress.status == ProgressStatus.COMPLETED

@pytest.mark.django_db
def test_manual_complete_lesson_unauthenticated(api_client, lesson_decorators):
    url = f"/api/v1/lessons/{lesson_decorators.id}/complete/"
    response = api_client.patch(url)
    
    assert response.status_code == 401

@pytest.mark.django_db
def test_manual_complete_idempotency(api_client, user_alice, lesson_decorators):
    api_client.force_authenticate(user=user_alice)
    
    # Complete once
    Progress.objects.create(
        user=user_alice,
        lesson=lesson_decorators,
        status=ProgressStatus.COMPLETED
    )
    
    url = f"/api/v1/lessons/{lesson_decorators.id}/complete/"
    response = api_client.patch(url)
    
    assert response.status_code == 200
    assert response.data["status"] == ProgressStatus.COMPLETED

@pytest.mark.django_db
def test_manual_complete_non_existent_lesson(api_client, user_alice):
    api_client.force_authenticate(user=user_alice)
    import uuid
    random_id = uuid.uuid4()
    
    url = f"/api/v1/lessons/{random_id}/complete/"
    response = api_client.patch(url)
    
    assert response.status_code == 404

@pytest.mark.django_db
def test_resume_course_completed_returns_first_of_many(api_client, user_alice, course_python, lesson_decorators, lesson_generators):
    api_client.force_authenticate(user=user_alice)
    
    # Complete both lessons
    Progress.objects.create(user=user_alice, lesson=lesson_decorators, status=ProgressStatus.COMPLETED)
    Progress.objects.create(user=user_alice, lesson=lesson_generators, status=ProgressStatus.COMPLETED)
    
    url = f"/api/v1/{course_python.slug}/resume/"
    response = api_client.get(url)
    
    assert response.status_code == 200
    # Should return lesson_decorators (order 1) not lesson_generators (order 2)
    assert response.data["lesson_slug"] == lesson_decorators.slug

@pytest.mark.django_db
def test_get_progress_by_lesson_id(api_client, user_alice, lesson_decorators):
    api_client.force_authenticate(user=user_alice)
    
    # Create progress
    Progress.objects.create(
        user=user_alice,
        lesson=lesson_decorators,
        status=ProgressStatus.COMPLETED
    )
    
    url = f"/api/v1/lessons/by-lesson/{lesson_decorators.id}/"
    response = api_client.get(url)
    
    assert response.status_code == 200
    assert response.data["status"] == ProgressStatus.COMPLETED