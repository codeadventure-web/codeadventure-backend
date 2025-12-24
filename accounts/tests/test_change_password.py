import pytest
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.mark.django_db
def test_change_password_success(api_client, user):
    # login first to get token
    login = api_client.post(
        "/api/v1/login/",
        {
            "username": "dao",
            "password": "pass1234",
        },
        format="json",
    )
    access = login.data["access"]
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")

    # Change password
    resp = api_client.put(
        "/api/v1/password/change/",
        {
            "old_password": "pass1234",
            "new_password": "newpass1234",
        },
        format="json",
    )
    assert resp.status_code == 200

    # Verify we can login with new password
    login = api_client.post(
        "/api/v1/login/",
        {
            "username": "dao",
            "password": "newpass1234",
        },
        format="json",
    )
    assert resp.status_code == 200
    assert "access" in login.data


@pytest.mark.django_db
def test_change_password_invalid_old_password(api_client, user):
    # login first to get token
    login = api_client.post(
        "/api/v1/login/",
        {
            "username": "dao",
            "password": "pass1234",
        },
        format="json",
    )
    access = login.data["access"]
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")

    # Change password with wrong old password
    resp = api_client.put(
        "/api/v1/password/change/",
        {
            "old_password": "wrongpassword",
            "new_password": "newpass1234",
        },
        format="json",
    )
    assert resp.status_code == 400
    assert "old_password" in resp.data


@pytest.mark.django_db
def test_change_password_requires_auth(api_client):
    resp = api_client.put(
        "/api/v1/password/change/",
        {
            "old_password": "pass1234",
            "new_password": "newpass1234",
        },
        format="json",
    )
    assert resp.status_code == 401
