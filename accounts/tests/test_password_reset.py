import pytest
from django.contrib.auth import get_user_model
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import smart_bytes
from django.contrib.auth.tokens import PasswordResetTokenGenerator

User = get_user_model()


@pytest.mark.django_db
def test_forgot_password_always_200(api_client, user, settings):
    settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
    resp = api_client.post(
        "/auth/password/forgot/",
        {
            "email": user.email,
        },
        format="json",
    )
    assert resp.status_code == 200
    # mail may or may not have been sent (fail_silently=True),
    # but at least the view doesn't leak user existence.


@pytest.mark.django_db
def test_reset_password_flow(api_client, user):
    token_gen = PasswordResetTokenGenerator()
    uidb64 = urlsafe_base64_encode(smart_bytes(user.pk))
    token = token_gen.make_token(user)

    resp = api_client.post(
        "/auth/password/reset/",
        {
            "uid": uidb64,
            "token": token,
            "new_password": "newpass123",
        },
        format="json",
    )
    assert resp.status_code == 200

    # login with new password
    login = api_client.post(
        "/auth/login/",
        {
            "username": user.username,
            "password": "newpass123",
        },
        format="json",
    )
    assert login.status_code == 200
