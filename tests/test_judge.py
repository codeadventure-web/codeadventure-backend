import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from judge.models import Language, Problem, TestCase


@pytest.mark.django_db
def test_submit_flow():
    User = get_user_model()
    u = User.objects.create_user("u1", password="pass")
    client = APIClient()
    client.force_authenticate(u)
    lang, _ = Language.objects.get_or_create(key="python", defaults={"version": "3.11"})
    prob, _ = Problem.objects.get_or_create(
        slug="sum-two", defaults={"title": "Sum Two", "statement_md": "..."}
    )
    TestCase.objects.get_or_create(
        problem=prob, input_data="1 2\n", expected_output="3\n", hidden=False
    )

    r = client.post(
        f"/api/v1/judge/submissions/problems/{prob.slug}/submit/",
        {"language_id": str(lang.id), "code": "print(sum(map(int,input().split())))"},
        format="json",
    )
    assert r.status_code in (200, 202)
