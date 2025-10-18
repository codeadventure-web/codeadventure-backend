import pytest
from django.urls import reverse
from rest_framework.test import APIClient

pytestmark = pytest.mark.django_db


def test_auth_register_login_me_refresh_logout_blacklist():
    c = APIClient()

    # register
    r = c.post(
        reverse("register"),
        {"username": "u1", "email": "u1@x.com", "password": "pass1234"},
        format="json",
    )
    assert r.status_code in (201, 400)  # ok if already exists

    # login
    r = c.post(
        reverse("login"), {"username": "u1", "password": "pass1234"}, format="json"
    )
    assert r.status_code == 200
    access = r.data["access"]
    refresh = r.data["refresh"]

    # me
    c.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
    r = c.get(reverse("me"))
    assert r.status_code == 200
    assert r.data["username"] == "u1"

    # refresh (get new access)
    c.credentials()  # clear
    r = c.post(reverse("token_refresh"), {"refresh": refresh}, format="json")
    assert r.status_code == 200
    new_access = r.data["access"]
    assert new_access and new_access != access

    # ✅ authenticate for logout
    c.credentials(HTTP_AUTHORIZATION=f"Bearer {new_access}")

    # logout (blacklist the original refresh)
    r = c.post(reverse("logout"), {"refresh": refresh}, format="json")
    assert r.status_code in (200, 205)

    # refresh again with blacklisted token -> 401
    r = c.post(reverse("token_refresh"), {"refresh": refresh}, format="json")
    assert r.status_code == 401
