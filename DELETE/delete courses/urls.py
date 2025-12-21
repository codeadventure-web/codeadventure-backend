from rest_framework.routers import SimpleRouter
from django.urls import path, include
from .views import CourseViewSet, LessonProgressView

router = SimpleRouter()
router.register(r"courses", CourseViewSet, basename="course")
router.register(r"lessons/progress", LessonProgressView, basename="progress")

urlpatterns = [path("", include(router.urls))]
