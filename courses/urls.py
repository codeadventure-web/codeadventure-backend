from django.urls import path
from .views import CourseViewSet, LessonProgressView, LessonView

course_list = CourseViewSet.as_view({"get": "list", "post": "create"})
course_detail = CourseViewSet.as_view(
    {"get": "retrieve", "put": "update", "patch": "partial_update", "delete": "destroy"}
)

urlpatterns = [
    path("courses/", course_list, name="course-list"),
    path(
        "lessons/progress/",
        LessonProgressView.as_view({"get": "list"}),
        name="progress-list",
    ),
    path("<slug:slug>/", course_detail, name="course-detail"),
    path(
        "<slug:course_slug>/<slug:lesson_slug>/",
        LessonView.as_view(),
        name="lesson-detail",
    ),
]
