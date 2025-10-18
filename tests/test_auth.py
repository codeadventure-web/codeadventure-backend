import pytest
from rest_framework.test import APIClient


@pytest.mark.django_db
def test_auth_flow():
    c = APIClient()
    r = c.post(
        "/api/v1/auth/register/",
        {"username": "u", "email": "u@x.com", "password": "pass1234"},
        format="json",
    )
    assert r.status_code in (201, 400)  # ok if already exists

    r = c.post(
        "/api/v1/auth/login/", {"username": "u", "password": "pass1234"}, format="json"
    )
    assert r.status_code == 200
    access = r.data["access"]

    c.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
    r = c.get("/api/v1/auth/me/")
    assert r.status_code == 200
    assert r.data["username"] == "u"
