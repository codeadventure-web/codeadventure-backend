from rest_framework import serializers
from .models import Language, TestCase


class LanguageSer(serializers.ModelSerializer):
    class Meta:
        model = Language
        fields = ("id", "key")


class TestCaseSer(serializers.ModelSerializer):
    class Meta:
        model = TestCase
        fields = ("id", "input_data", "expected_output", "hidden")


class SubmitSer(serializers.Serializer):
    language = serializers.CharField(max_length=20)
    code = serializers.CharField(min_length=1, max_length=100_000)

    def validate_code(self, value: str) -> str:
        if not value.strip():
            raise serializers.ValidationError("Code cannot be blank.")
        return value
