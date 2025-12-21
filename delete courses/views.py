from rest_framework import viewsets, mixins, permissions, decorators, response, filters
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Prefetch

from .models import Course, Progress
from .serializers import CourseListSer, CourseDetailSer, ProgressSer
from .filters import CourseFilter
from . import services
from common.permissions import IsTeacherOrReadOnly


class CourseViewSet(viewsets.ModelViewSet):
    queryset = Course.objects.all().order_by("title")
    permission_classes = [IsTeacherOrReadOnly]
    lookup_field = "slug"

    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_class = CourseFilter
    search_fields = ["title", "description"]
    ordering_fields = ["title", "created_at"]

    def get_serializer_class(self):
        return CourseDetailSer if self.action == "retrieve" else CourseListSer

    def get_queryset(self):
        qs = super().get_queryset()
        if self.action == "retrieve":
            qs = qs.prefetch_related("lessons")
            if self.request.user.is_authenticated:
                qs = qs.prefetch_related(
                    Prefetch(
                        "lessons__progress_set",
                        queryset=Progress.objects.filter(user=self.request.user),
                        to_attr="user_progress",
                    )
                )
        return qs

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        progress_map = {}

        if request.user.is_authenticated:
            for lesson in instance.lessons.all():
                if hasattr(lesson, "user_progress") and lesson.user_progress:
                    progress_map[lesson.id] = lesson.user_progress[0]

        context = self.get_serializer_context()
        context["progress_map"] = progress_map
        serializer = self.get_serializer(instance, context=context)
        return response.Response(serializer.data)


class LessonProgressView(
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    queryset = Progress.objects.all()
    serializer_class = ProgressSer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Progress.objects.filter(user=self.request.user)

    @decorators.action(
        detail=False, methods=["get"], url_path=r"by-lesson/(?P<lesson_id>[^/.]+)"
    )
    def by_lesson(self, request, lesson_id=None):
        prg, _ = services.get_or_create_progress(user=request.user, lesson_id=lesson_id)
        return response.Response(ProgressSer(prg).data)

    @decorators.action(
        detail=False, methods=["patch"], url_path=r"complete/(?P<lesson_id>[^/.]+)"
    )
    def complete(self, request, lesson_id=None):
        prg = services.complete_lesson_for_user(user=request.user, lesson_id=lesson_id)
        return response.Response(ProgressSer(prg).data)
