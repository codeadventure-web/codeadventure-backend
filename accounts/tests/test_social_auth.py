import pytest
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.mark.django_db
def test_google_login_creates_user(monkeypatch, api_client, settings):
    # pretend have a client id
    settings.GOOGLE_CLIENT_ID = "fake-client-id"

    def fake_verify(token, request, client_id):
        return {
            "iss": "accounts.google.com",
            "email": "googleuser@example.com",
            "given_name": "Google",
            "family_name": "User",
        }

    # patch google lib
    import accounts.serializers as accounts_serializers

    monkeypatch.setattr(
        accounts_serializers.google_id_token,
        "verify_oauth2_token",
        fake_verify,
    )

    resp = api_client.post(
        "/api/v1/social/google/",
        {
            "id_token": "fake-token",
        },
        format="json",
    )
    assert resp.status_code == 200
    assert resp.data["user"]["email"] == "googleuser@example.com"
    assert "access" in resp.data
    assert User.objects.filter(email="googleuser@example.com").count() == 1


@pytest.mark.django_db
def test_github_login_creates_user(monkeypatch, api_client):
    # fake GitHub /user
    def fake_get(url, headers=None, timeout=10):
        class R:
            status_code = 200

            def json(self_inner):
                if url.endswith("/user"):
                    return {
                        "id": 123,
                        "login": "gh-user",
                        "name": "GH User",
                        "email": None,
                    }
                else:
                    # /user/emails
                    return [
                        {
                            "email": "gh@example.com",
                            "primary": True,
                            "verified": True,
                        }
                    ]

        return R()

    import accounts.serializers as accounts_serializers

    monkeypatch.setattr(accounts_serializers.requests, "get", fake_get)

    resp = api_client.post(
        "/api/v1/social/github/",
        {
            "access_token": "gh-token",
        },
        format="json",
    )
    assert resp.status_code == 200
    assert resp.data["user"]["email"] == "gh@example.com"
    assert User.objects.filter(email="gh@example.com").exists()
