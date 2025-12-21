from rest_framework import (
    viewsets,
    mixins,
    permissions,
    decorators,
    response,
    filters,
    serializers,
)
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Prefetch
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny

from drf_spectacular.utils import extend_schema, inline_serializer
from .models import Course, Lesson, Progress
from .serializers import CourseListSer, CourseDetailSer, ProgressSer, LessonLiteSer
from .filters import CourseFilter
from . import services
from common.permissions import IsTeacherOrReadOnly
from common.enums import LessonType

from judge.models import Language, Submission
from judge.serializers import SubmitSer
from judge.runner_client import run_in_sandbox
from quizzes.models import QuizAttempt, QuizAnswer
from quizzes.serializers import AttemptSubmitSer
from quizzes.grading import grade_attempt
from rest_framework import status
from rest_framework.permissions import IsAuthenticated


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
            qs = qs.prefetch_related("lessons", "lessons__problem", "lessons__quiz")
            if self.request.user.is_authenticated:
                qs = qs.prefetch_related(
                    Prefetch(
                        "lessons__progress_set",
                        queryset=Progress.objects.filter(user=self.request.user),
                        to_attr="user_progress",
                    )
                )
        return qs

    @extend_schema(operation_id="v1_course_list")
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(operation_id="v1_course_create")
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @extend_schema(operation_id="v1_course_retrieve")
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

    @extend_schema(operation_id="v1_course_update")
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @extend_schema(operation_id="v1_course_partial_update")
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @extend_schema(operation_id="v1_course_destroy")
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)


class LessonProgressView(
    mixins.ListModelMixin,
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


class LessonView(APIView):
    def get_permissions(self):
        if self.request.method == "POST":
            return [IsAuthenticated()]
        return [AllowAny()]

    @extend_schema(
        operation_id="v1_lesson_detail",
        responses={200: LessonLiteSer},
        summary="Retrieve lesson details",
    )
    def get(self, request, course_slug=None, lesson_slug=None):
        course = get_object_or_404(Course, slug=course_slug)
        lesson = get_object_or_404(
            Lesson.objects.select_related("problem", "quiz"),
            course=course,
            slug=lesson_slug,
        )

        progress_map = {}
        if request.user.is_authenticated:
            progress_obj = Progress.objects.filter(
                user=request.user, lesson=lesson
            ).first()
            if progress_obj:
                progress_map[lesson.id] = progress_obj

        serializer = LessonLiteSer(lesson, context={"progress_map": progress_map})
        return Response(serializer.data)

    @extend_schema(
        operation_id="v1_lesson_submit",
        request=inline_serializer(
            name="LessonSubmitRequest",
            fields={
                "language_id": serializers.UUIDField(required=False),
                "code": serializers.CharField(required=False),
                "answers": serializers.ListField(required=False),
            },
        ),
        responses={
            201: inline_serializer(
                name="LessonSubmitResponse",
                fields={
                    "passed": serializers.BooleanField(),
                    "next_url": serializers.CharField(),
                    "submission_id": serializers.CharField(required=False),
                    "status": serializers.CharField(required=False),
                    "summary": serializers.JSONField(required=False),
                    "attempt_id": serializers.CharField(required=False),
                },
            )
        },
        summary="Submit lesson solution (code or quiz)",
    )
    def post(self, request, course_slug=None, lesson_slug=None):
        course = get_object_or_404(Course, slug=course_slug)
        lesson = get_object_or_404(
            Lesson.objects.select_related("problem", "quiz"),
            course=course,
            slug=lesson_slug,
        )

        if lesson.type == LessonType.JUDGE:
            return self.handle_judge(request, lesson)
        elif lesson.type == LessonType.QUIZ:
            return self.handle_quiz(request, lesson)
        else:
            return Response(
                {"error": "Unknown lesson type"}, status=status.HTTP_400_BAD_REQUEST
            )

    def get_next_url(self, course, lesson):
        next_lesson = lesson.get_next_lesson()
        if next_lesson:
            return f"/{course.slug}/{next_lesson.slug}/"
        return f"/{course.slug}/"

    def handle_judge(self, request, lesson):
        if not lesson.problem:
            return Response(
                {"error": "This lesson does not have a judge problem."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        ser = SubmitSer(data=request.data)
        ser.is_valid(raise_exception=True)

        lang = get_object_or_404(Language, id=ser.validated_data["language_id"])
        problem = lesson.problem

        if (
            problem.allowed_languages.exists()
            and not problem.allowed_languages.filter(id=lang.id).exists()
        ):
            return Response(
                {"language_id": ["This language is not allowed for this problem."]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        sub = Submission.objects.create(
            user=request.user,
            problem=problem,
            language=lang,
            code=ser.validated_data["code"],
            status="running",
        )

        # Run synchronously
        result = run_in_sandbox(sub)

        sub.status = result["final_status"]
        sub.summary = result
        sub.save(update_fields=["status", "summary"])

        # If Accepted, complete the lesson
        passed = sub.status == "ac"
        if passed:
            services.complete_lesson_for_user(request.user, lesson.id)

        next_url = self.get_next_url(lesson.course, lesson)

        return Response(
            {
                "passed": passed,
                "next_url": next_url,
                "submission_id": str(sub.id),
                "status": sub.status,
                "summary": sub.summary,
            },
            status=status.HTTP_201_CREATED,
        )

    def handle_quiz(self, request, lesson):
        if not lesson.quiz:
            return Response(
                {"error": "This lesson does not have a quiz."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        quiz_obj = lesson.quiz

        ser = AttemptSubmitSer(data=request.data)
        ser.is_valid(raise_exception=True)

        # Create Attempt
        attempt = QuizAttempt.objects.create(user=request.user, quiz=quiz_obj)

        # Save answers
        answers_data = ser.validated_data["answers"]
        for ans_data in answers_data:
            QuizAnswer.objects.create(
                attempt=attempt,
                question=ans_data["question"],
                selected_choice_ids=ans_data["selected_choice_ids"],
            )

        # Grade
        grade_attempt(attempt)

        passed = attempt.is_passed
        if passed:
            services.complete_lesson_for_user(request.user, lesson.id)

        next_url = self.get_next_url(lesson.course, lesson)

        return Response(
            {
                "passed": passed,
                "next_url": next_url,
                "attempt_id": str(attempt.id),
            },
            status=status.HTTP_201_CREATED,
        )
