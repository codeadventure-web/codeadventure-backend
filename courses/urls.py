from django.urls import path
from .views import CourseViewSet, LessonProgressView, LessonView

course_list = CourseViewSet.as_view({"get": "list", "post": "create"})
course_detail = CourseViewSet.as_view(
    {
        "get": "retrieve",
        "put": "update",
        "patch": "partial_update",
        "delete": "destroy",
    }
)
course_resume = CourseViewSet.as_view({"get": "resume"})
course_my = CourseViewSet.as_view({"get": "my_courses"})

urlpatterns = [
    path("courses/my/", course_my, name="course-my"),
    path("courses/", course_list, name="course-list"),
    path(
        "lessons/progress/",
        LessonProgressView.as_view({"get": "list"}),
        name="progress-list",
    ),
    path(
        "lessons/by-lesson/<uuid:lesson_id>/",
        LessonProgressView.as_view({"get": "by_lesson"}),
        name="progress-by-lesson",
    ),
    path(
        "lessons/<uuid:lesson_id>/complete/",
        LessonProgressView.as_view({"patch": "complete"}),
        name="lesson-complete",
    ),
    path("<slug:slug>/resume/", course_resume, name="course-resume"),
    path("<slug:slug>/", course_detail, name="course-detail"),
    path(
        "<slug:course_slug>/<slug:lesson_slug>/",
        LessonView.as_view(),
        name="lesson-detail",
    ),
]
