from rest_framework import serializers
from .models import Quiz, Question, Choice, QuizAnswer


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


class QuizAnswerSer(serializers.ModelSerializer):
    class Meta:
        model = QuizAnswer
        fields = ("question", "selected_choice_ids")


class AttemptSubmitSer(serializers.Serializer):
    answers = QuizAnswerSer(many=True)
