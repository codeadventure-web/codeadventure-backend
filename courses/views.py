from rest_framework import viewsets, mixins, permissions, decorators, response, status
from django.shortcuts import get_object_or_404
from .models import Course, Section, Lesson, Enrollment, Progress
from .serializers import CourseListSer, CourseDetailSer, ProgressSer
from common.permissions import IsAdminOrReadOnly


class CourseViewSet(viewsets.ModelViewSet):
    queryset = Course.objects.all().order_by("title")
    permission_classes = [IsAdminOrReadOnly]
    lookup_field = "slug"

    def get_serializer_class(self):
        return CourseDetailSer if self.action in ["retrieve"] else CourseListSer

    filterset_fields = ["is_published"]
    search_fields = ["title", "description"]
    ordering_fields = ["title", "created_at"]

    @decorators.action(
        detail=True, methods=["post"], permission_classes=[permissions.IsAuthenticated]
    )
    def enroll(self, request, slug=None):
        course = self.get_object()
        Enrollment.objects.get_or_create(
            user=request.user, course=course, defaults={"active": True}
        )
        return response.Response({"enrolled": True})


class LessonProgressView(
    mixins.RetrieveModelMixin, mixins.UpdateModelMixin, viewsets.GenericViewSet
):
    queryset = Progress.objects.all()
    serializer_class = ProgressSer
    permission_classes = [permissions.IsAuthenticated]

    @decorators.action(
        detail=False, methods=["get"], url_path=r"by-lesson/(?P<lesson_id>[^/.]+)"
    )
    def by_lesson(self, request, lesson_id=None):
        prg, _ = Progress.objects.get_or_create(user=request.user, lesson_id=lesson_id)
        return response.Response(ProgressSer(prg).data)

    @decorators.action(
        detail=False, methods=["patch"], url_path=r"complete/(?P<lesson_id>[^/.]+)"
    )
    def complete(self, request, lesson_id=None):
        prg, _ = Progress.objects.get_or_create(user=request.user, lesson_id=lesson_id)
        prg.status = "completed"
        prg.save(update_fields=["status"])
        return response.Response(ProgressSer(prg).data)
