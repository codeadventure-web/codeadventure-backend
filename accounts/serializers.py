import requests
from rest_framework import serializers
from .models import User, Profile
from django.db import transaction
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.encoding import force_str, smart_bytes
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth import get_user_model


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ("avatar", "bio")


class UserMeSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer()

    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "email",
            "role",
            "first_name",
            "last_name",
            "profile",
        )

    @transaction.atomic
    def update(self, instance, validated):
        profile_data = validated.pop("profile", None)
        for k, v in validated.items():
            setattr(instance, k, v)
        instance.save()
        if profile_data:
            Profile.objects.update_or_create(user=instance, defaults=profile_data)
        return instance


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)

    class Meta:
        model = User
        fields = ("username", "email", "password")

    def create(self, data):
        return User.objects.create_user(**data)


class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        # don't leak whether user exists
        return value

    def save(self, **kwargs):
        email = self.validated_data["email"]
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return

        token_gen = PasswordResetTokenGenerator()
        uidb64 = urlsafe_base64_encode(smart_bytes(user.pk))
        token = token_gen.make_token(user)

        # frontend URL for password reset
        frontend_url = getattr(
            settings,
            "FRONTEND_RESET_PASSWORD_URL",
            "https://codeadventure/reset-password",
        )
        reset_link = f"{frontend_url}?uid={uidb64}&token={token}"

        subject = "Reset your CodeAdventure password"
        message = f"Hi {user.username},\n\nClick the link below to reset your password:\n{reset_link}\n\nIf you didn't request this, ignore this email."
        from_email = getattr(settings, "DEFAULT_FROM_EMAIL", None)

        # if email backend is not configured, this will just be a no-op in console/email backend
        send_mail(subject, message, from_email, [email], fail_silently=True)


class ResetPasswordSerializer(serializers.Serializer):
    uid = serializers.CharField()
    token = serializers.CharField()
    new_password = serializers.CharField(min_length=6, write_only=True)

    def validate(self, attrs):
        uid = attrs.get("uid")
        token = attrs.get("token")

        try:
            user_id = force_str(urlsafe_base64_decode(uid))
            user = User.objects.get(pk=user_id)
        except Exception:
            raise serializers.ValidationError("Invalid uid or token")

        token_gen = PasswordResetTokenGenerator()
        if not token_gen.check_token(user, token):
            raise serializers.ValidationError("Invalid or expired token")

        # keep user for save()
        attrs["user"] = user
        return attrs

    def save(self, **kwargs):
        user = self.validated_data["user"]
        password = self.validated_data["new_password"]
        user.set_password(password)
        user.save()
        return user


User = get_user_model()


class GoogleLoginSerializer(serializers.Serializer):
    id_token = serializers.CharField()

    def validate(self, attrs):
        from google.oauth2 import id_token as google_id_token
        from google.auth.transport import requests

        token = attrs.get("id_token")
        try:
            idinfo = google_id_token.verify_oauth2_token(
                token,
                requests.Request(),
                # put your Google client ID here (web client id)
                getattr(settings, "GOOGLE_CLIENT_ID", None),
            )
        except Exception:
            raise serializers.ValidationError("Invalid Google token")

        if idinfo.get("iss") not in [
            "accounts.google.com",
            "https://accounts.google.com",
        ]:
            raise serializers.ValidationError("Invalid issuer")

        email = idinfo.get("email")
        if not email:
            raise serializers.ValidationError("Google account has no email")

        attrs["google_data"] = idinfo
        attrs["email"] = email
        return attrs

    def create_or_get_user(self):
        email = self.validated_data["email"]
        google_data = self.validated_data["google_data"]

        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                "username": email.split("@")[0],
                "first_name": google_data.get("given_name", ""),
                "last_name": google_data.get("family_name", ""),
            },
        )
        return user


class GithubLoginSerializer(serializers.Serializer):
    access_token = serializers.CharField()

    def validate(self, attrs):
        access_token = attrs.get("access_token")

        # 1. get user basic info
        user_resp = requests.get(
            "https://api.github.com/user",
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=10,
        )
        if user_resp.status_code != 200:
            raise serializers.ValidationError("Invalid GitHub token")

        user_data = user_resp.json()
        github_id = user_data.get("id")
        github_login = user_data.get("login")
        name = user_data.get("name") or ""
        # fallback to name split
        first_name = name.split(" ")[0] if name else ""
        last_name = " ".join(name.split(" ")[1:]) if name and " " in name else ""

        # get emails to find primary/verified
        email = None
        emails_resp = requests.get(
            "https://api.github.com/user/emails",
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=10,
        )
        if emails_resp.status_code == 200:
            for item in emails_resp.json():
                if item.get("primary") and item.get("verified"):
                    email = item.get("email")
                    break

        # GitHub users can hide email => create placeholder
        if not email:
            email = user_data.get("email")

        if not email:
            # raise serializers.ValidationError("GitHub account has no public email")
            email = f"{github_login or github_id}@github.local"

        attrs["github_data"] = user_data
        attrs["email"] = email
        attrs["first_name"] = first_name
        attrs["last_name"] = last_name
        attrs["username_guess"] = github_login or (email.split("@")[0])
        return attrs

    def create_or_get_user(self):
        email = self.validated_data["email"]
        first_name = self.validated_data["first_name"]
        last_name = self.validated_data["last_name"]
        username_guess = self.validated_data["username_guess"]

        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                "username": username_guess,
                "first_name": first_name,
                "last_name": last_name,
            },
        )
        return user
