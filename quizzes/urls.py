from django.urls import path
from .views import (
    QuizListCreateView,
    QuizRetrieveUpdateDelete,
    AttemptStartView,
    AttemptSubmitView,
    QuestionListCreateView,
    QuestionRetrieveUpdateDelete,
)

urlpatterns = [
    path("quizzes/", QuizListCreateView.as_view()), # List
    path("quiz/<uuid:id>/", QuizRetrieveUpdateDelete.as_view()), # GET /quiz/quiz_id/
    path("quiz/<uuid:quiz_id>/questions/", QuestionListCreateView.as_view()),
    path("quiz/question/<uuid:id>/", QuestionRetrieveUpdateDelete.as_view()),
    path("quiz/<uuid:lesson_id>/attempts/", AttemptStartView.as_view()),
    path("quiz/attempts/<uuid:attempt_id>/submit/", AttemptSubmitView.as_view()),
]