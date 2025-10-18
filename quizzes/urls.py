from django.urls import path
from .views import (
    QuizDetailView,
    AttemptStartView,
    AttemptSubmitView,
    AttemptResultView,
)

urlpatterns = [
    path("quizzes/<uuid:lesson_id>/", QuizDetailView.as_view()),
    path("quizzes/<uuid:lesson_id>/attempts/", AttemptStartView.as_view()),
    path("quizzes/attempts/<uuid:attempt_id>/submit/", AttemptSubmitView.as_view()),
    path("quizzes/attempts/<uuid:id>/", AttemptResultView.as_view()),
]
