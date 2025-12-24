import pytest
from unittest.mock import patch
from courses.models import Progress, Lesson
from common.enums import ProgressStatus, LessonType
from quizzes.models import Question, Choice


@pytest.mark.django_db
def test_submission_updates_progress_and_returns_next_url(
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
    l2 = Lesson.objects.create(
        course=course_python,
        title="L2",
        order=2,
        type=LessonType.JUDGE,
        problem=problem_python,
    )

    api_client.force_authenticate(user=user_alice)

    url = f"/api/v1/{course_python.slug}/{l1.slug}/"

    # Payload
    data = {"language_id": language_python.id, "code": "print(1+1)"}

    # Mock sandbox to return 'ac' (Accepted)
    with patch("courses.views.run_in_sandbox") as mock_run:
        mock_run.return_value = {
            "final_status": "ac",
            "stdout": "2",
            "stderr": "",
            "exit_code": 0,
        }

        response = api_client.post(url, data, format="json")

    assert response.status_code == 201
    assert response.data["passed"] is True

    # Check Progress in Response
    assert "progress" in response.data
    assert response.data["progress"]["status"] == ProgressStatus.COMPLETED

    # Check Next URL
    # Should point to Lesson 2
    expected_next = f"/{course_python.slug}/{l2.slug}/"
    assert response.data["next_url"] == expected_next

    # Verify DB
    p = Progress.objects.get(user=user_alice, lesson=l1)
    assert p.status == ProgressStatus.COMPLETED


@pytest.mark.django_db
def test_submission_failed_does_not_complete(
    api_client, user_alice, course_python, problem_python, language_python
):
    l1 = Lesson.objects.create(
        course=course_python,
        title="L1",
        order=1,
        type=LessonType.JUDGE,
        problem=problem_python,
    )

    api_client.force_authenticate(user=user_alice)
    url = f"/api/v1/{course_python.slug}/{l1.slug}/"
    data = {"language_id": language_python.id, "code": "error"}

    with patch("courses.views.run_in_sandbox") as mock_run:
        mock_run.return_value = {
            "final_status": "wa",  # Wrong Answer
            "stdout": "0",
            "stderr": "",
            "exit_code": 0,
        }

        response = api_client.post(url, data, format="json")

    assert response.status_code == 201
    assert response.data["passed"] is False

    # Check Progress in Response (Should be incomplete)
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
