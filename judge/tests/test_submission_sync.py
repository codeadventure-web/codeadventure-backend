import pytest
from unittest.mock import patch
from courses.models import Progress
from common.enums import ProgressStatus


@pytest.mark.django_db
def test_sync_submission_completes_lesson(
    api_client,
    user_student,
    problem_sum,
    lang_python,
    lesson_with_problem,
    course_python,
):
    api_client.force_authenticate(user=user_student)

    # Mock the sandbox runner to return AC
    with patch("courses.views.run_in_sandbox") as mock_run:
        mock_run.return_value = {
            "final_status": "ac",
            "tests": [],
            "compile_output": "",
        }

        url = f"/api/v1/{course_python.slug}/{lesson_with_problem.slug}/"
        data = {"language_id": str(lang_python.id), "code": "print(sum)"}

        resp = api_client.post(url, data, format="json")

        assert resp.status_code == 201
        assert resp.data["status"] == "ac"
        assert resp.data["passed"] is True
        # No next lesson, so should point to course home
        assert resp.data["next_url"] == f"/{course_python.slug}/"

        # Verify Progress created and completed
        progress = Progress.objects.get(user=user_student, lesson=lesson_with_problem)
        assert progress.status == ProgressStatus.COMPLETED


@pytest.mark.django_db
def test_sync_submission_fails_lesson(
    api_client,
    user_student,
    problem_sum,
    lang_python,
    lesson_with_problem,
    course_python,
):
    api_client.force_authenticate(user=user_student)

    # Mock the sandbox runner to return WA (Wrong Answer)
    with patch("courses.views.run_in_sandbox") as mock_run:
        mock_run.return_value = {
            "final_status": "wa",
            "tests": [],
            "compile_output": "",
        }

        url = f"/api/v1/{course_python.slug}/{lesson_with_problem.slug}/"
        data = {"language_id": str(lang_python.id), "code": "print('wrong')"}

        resp = api_client.post(url, data, format="json")

        assert resp.status_code == 201
        assert resp.data["status"] == "wa"

        # Progress should NOT be completed (or not exist if first try)
        # Note: get_or_create might have happened if viewed, but let's check status
        progress_exists = Progress.objects.filter(
            user=user_student, lesson=lesson_with_problem
        ).exists()
        if progress_exists:
            p = Progress.objects.get(user=user_student, lesson=lesson_with_problem)
            assert p.status != ProgressStatus.COMPLETED
