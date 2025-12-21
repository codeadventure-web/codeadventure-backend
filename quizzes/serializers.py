from rest_framework import serializers
from .models import Quiz, QuizAttempt


class QuizSerializer(serializers.ModelSerializer):
    class Meta:
        model = Quiz
        fields = "__all__"


class AttemptSubmitSerializer(serializers.Serializer):
    answers = serializers.DictField(
        child=serializers.ListField(
            child=serializers.CharField()
        )
    )


class AttemptResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuizAttempt
        fields = ["id", "score", "total", "answers"]
