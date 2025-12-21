from rest_framework import serializers
from .models import Quiz, Question, Choice, QuizAttempt, QuizAnswer


class ChoiceSer(serializers.ModelSerializer):
    class Meta:
        model = Choice
        fields = ("id", "text")


class QuestionSer(serializers.ModelSerializer):
    choices = ChoiceSer(many=True, read_only=True)

    class Meta:
        model = Question
        fields = ("id", "text", "type", "choices")


class QuizSer(serializers.ModelSerializer):
    questions = QuestionSer(many=True, read_only=True)

    class Meta:
        model = Quiz
        fields = ("id", "lesson", "questions")


class QuizAnswerSer(serializers.ModelSerializer):
    class Meta:
        model = QuizAnswer
        fields = ("question", "selected_choice_ids")


class AttemptCreateSer(serializers.Serializer):
    pass


class AttemptSubmitSer(serializers.Serializer):
    answers = QuizAnswerSer(many=True)


class AttemptResultSer(serializers.ModelSerializer):
    class Meta:
        model = QuizAttempt
        fields = ("id", "score", "finished")
