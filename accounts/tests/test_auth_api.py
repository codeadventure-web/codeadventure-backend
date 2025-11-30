import pytest
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.mark.django_db
def test_register(api_client):
    resp = api_client.post(
        "/auth/register/",
        {
            "username": "newuser",
            "email": "new@example.com",
            "password": "pass1234",
        },
        format="json",
    )
    assert resp.status_code == 201
    assert User.objects.filter(username="newuser").exists()


@pytest.mark.django_db
def test_login(api_client, user):
    resp = api_client.post(
        "/auth/login/",
        {
            "username": "dao",
            "password": "pass1234",
        },
        format="json",
    )
    assert resp.status_code == 200
    assert "access" in resp.data
    assert "refresh" in resp.data
    assert "user" in resp.data


@pytest.mark.django_db
def test_me_requires_auth(api_client):
    resp = api_client.get("/auth/me/")
    assert resp.status_code == 401  # IsAuthenticated


@pytest.mark.django_db
def test_me_get_and_patch(api_client, user):
    # login first to get token
    login = api_client.post(
        "/auth/login/",
        {
            "username": "dao",
            "password": "pass1234",
        },
        format="json",
    )
    access = login.data["access"]
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")

    # GET
    resp = api_client.get("/auth/me/")
    assert resp.status_code == 200
    assert resp.data["username"] == "dao"

    # PATCH with profile
    resp = api_client.patch(
        "/auth/me/",
        {
            "first_name": "Dao",
            "profile": {
                "bio": "Hi!",
                "avatar": "https://example.com/a.png",
            },
        },
        format="json",
    )
    assert resp.status_code == 200
    assert resp.data["first_name"] == "Dao"
    assert resp.data["profile"]["bio"] == "Hi!"


# test safe logout
@pytest.mark.django_db
def test_safe_logout_accepts_invalid_token(api_client):
    resp = api_client.post("/auth/logout/", {"refresh": "totally-invalid"})
    # should still succeed with 205
    assert resp.status_code == 205
