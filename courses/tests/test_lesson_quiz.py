import pytest
from common.enums import LessonType, ProgressStatus
from courses.models import Lesson, Progress
from quizzes.models import Quiz, Question, Choice


@pytest.fixture
def quiz_lesson(db, course_python):
    quiz = Quiz.objects.create(title="Python Basics Quiz")
    q1 = Question.objects.create(quiz=quiz, text="What is 1+1?")
    c1 = Choice.objects.create(question=q1, text="2", is_answer=True)
    c2 = Choice.objects.create(question=q1, text="3", is_answer=False)

    lesson = Lesson.objects.create(
        course=course_python,
        title="Quiz Lesson",
        order=20,
        type=LessonType.QUIZ,
        quiz=quiz,
    )

    # Add a next lesson
    Lesson.objects.create(
        course=course_python, title="Next Lesson", order=21, content_md="Next..."
    )

    return lesson, q1, c1, c2


@pytest.mark.django_db
def test_lesson_detail_includes_quiz_data(api_client, course_python, quiz_lesson):
    lesson, q1, c1, c2 = quiz_lesson
    url = f"/{course_python.slug}/{lesson.slug}/"  # Using the root URL config

    # Need to restore URL prefix if previously reverted?
    # Current state: /api/v1/ prefix was restored.
    url = f"/api/v1/{course_python.slug}/{lesson.slug}/"

    resp = api_client.get(url)
    assert resp.status_code == 200
    data = resp.data

    assert data["type"] == LessonType.QUIZ
    assert data["quiz"] is not None
    assert len(data["quiz"]["questions"]) == 1
    assert data["quiz"]["questions"][0]["text"] == "What is 1+1?"
    assert len(data["quiz"]["questions"][0]["choices"]) == 2
    assert "is_answer" in data["quiz"]["questions"][0]["choices"][0]


@pytest.mark.django_db
def test_quiz_submission_success(api_client, user_alice, course_python, quiz_lesson):
    lesson, q1, c1, c2 = quiz_lesson
    api_client.force_authenticate(user=user_alice)

    url = f"/api/v1/{course_python.slug}/{lesson.slug}/"

    # Correct answer
    data = {"answers": [{"question": str(q1.id), "selected_choice_id": str(c1.id)}]}

    resp = api_client.post(url, data, format="json")
    assert resp.status_code == 201
    assert resp.data["passed"] is True
    # Should point to next lesson: /course-slug/21/
    assert resp.data["next_url"] == f"/{course_python.slug}/21/"

    # Verify lesson completion
    prog = Progress.objects.get(user=user_alice, lesson=lesson)
    assert prog.status == ProgressStatus.COMPLETED


@pytest.mark.django_db
def test_quiz_submission_failure(api_client, user_alice, course_python, quiz_lesson):
    lesson, q1, c1, c2 = quiz_lesson
    api_client.force_authenticate(user=user_alice)

    url = f"/api/v1/{course_python.slug}/{lesson.slug}/"

    # Incorrect answer
    data = {"answers": [{"question": str(q1.id), "selected_choice_id": str(c2.id)}]}

    resp = api_client.post(url, data, format="json")
    assert resp.status_code == 201
    assert resp.data["passed"] is False

    # Verify lesson NOT completed
    # Progress might be created but status INCOMPLETE
    prog_exists = Progress.objects.filter(user=user_alice, lesson=lesson).exists()
    if prog_exists:
        prog = Progress.objects.get(user=user_alice, lesson=lesson)
        assert prog.status != ProgressStatus.COMPLETED
