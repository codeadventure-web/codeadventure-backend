from rest_framework.routers import SimpleRouter
from django.urls import path, include
from .views import LanguageViewSet, ProblemViewSet, SubmissionViewSet

router = SimpleRouter()
router.register(r"judge/languages", LanguageViewSet, basename="language")
router.register(r"judge/problems", ProblemViewSet, basename="problem")
router.register(r"judge/submissions", SubmissionViewSet, basename="submission")

urlpatterns = [path("", include(router.urls))]
