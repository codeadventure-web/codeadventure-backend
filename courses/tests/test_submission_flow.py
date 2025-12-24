import pytest
from unittest.mock import patch
from courses.models import Progress, Lesson
from common.enums import ProgressStatus, LessonType
from quizzes.models import Question, Choice


@pytest.mark.django_db
def test_submission_returns_queued_status(
    api_client, user_alice, course_python, problem_python, language_python
):
    # Setup lessons
    l1 = Lesson.objects.create(
        course=course_python,
        title="L1",
        order=1,
        type=LessonType.JUDGE,
        problem=problem_python,
    )

    api_client.force_authenticate(user=user_alice)

    url = f"/api/v1/{course_python.slug}/{l1.slug}/"

    # Payload
    data = {"language": language_python.key, "code": "print(1+1)"}

    # Mock celery task
    with patch("judge.tasks.run_submission.delay") as mock_delay:
        response = api_client.post(url, data, format="json")
        mock_delay.assert_called_once()

    assert response.status_code == 201
    # Since it's async, it returns queued and passed=False initially
    assert response.data["passed"] is False
    assert response.data["status"] == "queued"

    # Check Progress in Response (Should be INCOMPLETE)
    assert "progress" in response.data
    assert response.data["progress"]["status"] == ProgressStatus.INCOMPLETE

    # Verify DB
    p = Progress.objects.get(user=user_alice, lesson=l1)
    assert p.status == ProgressStatus.INCOMPLETE


@pytest.mark.django_db
def test_quiz_submission_updates_progress(
    api_client, user_alice, course_python, quiz_python
):
    # Setup Quiz
    q1 = Question.objects.create(quiz=quiz_python, text="What is 1+1?")
    c1 = Choice.objects.create(question=q1, text="2", is_answer=True)
    Choice.objects.create(question=q1, text="3", is_answer=False)

    # Setup Lesson
    l1 = Lesson.objects.create(
        course=course_python,
        title="Quiz Lesson",
        order=1,
        type=LessonType.QUIZ,
        quiz=quiz_python,
    )

    api_client.force_authenticate(user=user_alice)
    url = f"/api/v1/{course_python.slug}/{l1.slug}/"

    # Correct Answer
    data = {"answers": [{"question": str(q1.id), "selected_choice_id": str(c1.id)}]}

    response = api_client.post(url, data, format="json")

    assert response.status_code == 201
    assert response.data["passed"] is True
    assert response.data["progress"]["status"] == ProgressStatus.COMPLETED

    # Verify DB
    p = Progress.objects.get(user=user_alice, lesson=l1)
    assert p.status == ProgressStatus.COMPLETED


@pytest.mark.django_db
def test_quiz_submission_failure(api_client, user_alice, course_python, quiz_python):
    # Setup Quiz
    q1 = Question.objects.create(quiz=quiz_python, text="What is 1+1?")
    Choice.objects.create(question=q1, text="2", is_answer=True)
    c2 = Choice.objects.create(question=q1, text="3", is_answer=False)

    # Setup Lesson
    l1 = Lesson.objects.create(
        course=course_python,
        title="Quiz Lesson",
        order=1,
        type=LessonType.QUIZ,
        quiz=quiz_python,
    )

    api_client.force_authenticate(user=user_alice)
    url = f"/api/v1/{course_python.slug}/{l1.slug}/"

    # Wrong Answer
    data = {"answers": [{"question": str(q1.id), "selected_choice_id": str(c2.id)}]}

    response = api_client.post(url, data, format="json")

    assert response.status_code == 201
    assert response.data["passed"] is False
    assert response.data["progress"]["status"] == ProgressStatus.INCOMPLETE
