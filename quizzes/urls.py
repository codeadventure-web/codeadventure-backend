from django.urls import path
from .views import (
    QuizListCreateView,
    QuizRetrieveUpdateDelete,
    AttemptStartView,
    AttemptSubmitView,
    AttemptResultView,
    QuestionListCreateView,
    QuestionRetrieveUpdateDelete,
    ChoiceListCreateView,
    ChoiceRetrieveUpdateDelete
)

urlpatterns = [
    path("quizzes/", QuizListCreateView.as_view()),
    path("quiz/<uuid:lesson_id>/", QuizRetrieveUpdateDelete.as_view()),
    path("quiz/<uuid:quiz_id>/questions", QuestionListCreateView.as_view()),
    path("quiz/question/<uuid:id>" ,QuestionRetrieveUpdateDelete.as_view()),
    path("question/<uuid:question_id>/choices" ,ChoiceListCreateView.as_view()),
    path("choice/<uuid:id>/", ChoiceRetrieveUpdateDelete.as_view()),
    path("quiz/<uuid:lesson_id>/attempts/", AttemptStartView.as_view()),
    path("quiz/attempts/<uuid:attempt_id>/submit/", AttemptSubmitView.as_view()),
    path("quiz/attempts/<uuid:id>/", AttemptResultView.as_view()),
]
