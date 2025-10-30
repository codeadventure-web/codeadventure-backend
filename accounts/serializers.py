from rest_framework import serializers
from .models import User, Profile
from django.db import transaction
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.encoding import force_str, smart_bytes
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.core.mail import send_mail
from django.conf import settings


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
