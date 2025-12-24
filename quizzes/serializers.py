from rest_framework import serializers
from .models import Quiz, Question, Choice


class ChoiceSer(serializers.ModelSerializer):
    class Meta:
        model = Choice
        fields = ("id", "text")


class QuestionSer(serializers.ModelSerializer):
    choices = ChoiceSer(many=True, read_only=True)

    class Meta:
        model = Question
        fields = ("id", "text", "choices")


class QuizSer(serializers.ModelSerializer):
    questions = QuestionSer(many=True, read_only=True)

    class Meta:
        model = Quiz
        fields = ("id", "questions")


class QuizAnswerSer(serializers.Serializer):
    question = serializers.UUIDField()
    selected_choice_id = serializers.UUIDField()


class AttemptSubmitSer(serializers.Serializer):
    answers = QuizAnswerSer(many=True)
