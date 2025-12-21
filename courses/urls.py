from rest_framework.routers import SimpleRouter
from django.urls import path, include
from .views import CourseViewSet, LessonProgressView, LessonDetailView

router = SimpleRouter()
router.register(r"courses", CourseViewSet, basename="course")
router.register(r"lessons/progress", LessonProgressView, basename="progress")

urlpatterns = [
    path("", include(router.urls)),
    # Chi tiết lesson theo lesson_id trong course
    path(
        "courses/<str:course_slug>/lessons/<uuid:lesson_id>/",
        LessonDetailView.as_view(),
        name="lesson-detail",
    ),
]