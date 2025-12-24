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
from .serializers import (
    CourseListSer,
    CourseDetailSer,
    ProgressSer,
    ProgressLiteSer,
    LessonLiteSer,
    LessonSerializer,
    MyCourseSerializer,
)
from .filters import CourseFilter
from . import services
from common.permissions import IsTeacherOrReadOnly
from common.enums import LessonType, ProgressStatus

from judge.models import Language, Submission
from judge.serializers import SubmitSer
from judge.runner_client import run_in_sandbox
from quizzes.serializers import AttemptSubmitSer
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
import logging

logger = logging.getLogger(__name__)


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

    @extend_schema(
        tags=["Courses"],
        summary="List all courses",
        description="Returns a paginated list of all available courses. Supports filtering by publication status and searching by title or description.",
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(
        tags=["Courses"],
        summary="Create a new course",
        description="Creates a new course. Restricted to users with teaching/staff permissions.",
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @extend_schema(
        tags=["Courses"],
        summary="Retrieve course details (with lessons)",
        description="Returns detailed information about a single course, including its list of lessons. If the user is authenticated, it also includes their progress for each lesson.",
    )
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

    @extend_schema(
        tags=["Courses"],
        summary="Update a course",
        description="Updates an existing course. Restricted to teachers/staff.",
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @extend_schema(
        tags=["Courses"],
        summary="Partially update a course",
        description="Partially updates an existing course. Restricted to teachers/staff.",
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @extend_schema(
        tags=["Courses"],
        summary="Delete a course",
        description="Deletes an existing course. Restricted to teachers/staff.",
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)

    @extend_schema(
        tags=["Courses"],
        summary="List enrolled courses with progress",
        responses={200: MyCourseSerializer(many=True)},
    )
    @decorators.action(
        detail=False, methods=["get"], permission_classes=[IsAuthenticated]
    )
    def my_courses(self, request):
        # Get all courses where user has any progress
        course_ids = (
            Progress.objects.filter(user=request.user)
            .values_list("lesson__course_id", flat=True)
            .distinct()
        )

        enrolled_courses = Course.objects.filter(id__in=course_ids)

        results = []
        for course in enrolled_courses:
            total_lessons = course.lessons.count()
            if total_lessons == 0:
                completed_lessons = 0
                percentage = 0
            else:
                completed_lessons = Progress.objects.filter(
                    user=request.user,
                    lesson__course=course,
                    status=ProgressStatus.COMPLETED,
                ).count()
                percentage = int((completed_lessons / total_lessons) * 100)

            is_completed = percentage == 100 and total_lessons > 0

            results.append(
                {
                    "id": course.id,
                    "title": course.title,
                    "slug": course.slug,
                    "completion_percentage": percentage,
                    "is_completed": is_completed,
                }
            )

        serializer = MyCourseSerializer(results, many=True)
        return Response(serializer.data)

    @extend_schema(
        tags=["Courses"],
        summary="Resume course",
        description="Returns the slug of the next incomplete lesson for the user, or the first lesson if none started.",
        responses={
            200: inline_serializer(
                name="ResumeResponse", fields={"lesson_slug": serializers.CharField()}
            )
        },
    )
    @decorators.action(
        detail=True, methods=["get"], permission_classes=[IsAuthenticated]
    )
    def resume(self, request, slug=None):
        course = self.get_object()
        # Get all lessons ordered
        lessons = course.lessons.all().order_by("order")

        # Get completed lesson IDs
        completed_ids = Progress.objects.filter(
            user=request.user, lesson__course=course, status=ProgressStatus.COMPLETED
        ).values_list("lesson_id", flat=True)

        # Find first lesson not in completed_ids
        next_lesson = None
        for lesson in lessons:
            if lesson.id not in completed_ids:
                next_lesson = lesson
                break

        # If all completed, maybe return the last one? Or null?
        # User requirement: "just click to continue".
        # If finished, probably take them to the last one or stay there.
        # Let's return the first one if all completed (review) or just the last one.
        if not next_lesson and lessons.exists():
            next_lesson = lessons.first()

        if not next_lesson:
            return Response(
                {"detail": "No lessons in this course."},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response({"lesson_slug": next_lesson.slug})


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

    @extend_schema(
        tags=["Progress"],
        summary="Get progress by lesson ID",
        description="Retrieves the completion status of a specific lesson for the authenticated user.",
    )
    @decorators.action(
        detail=False, methods=["get"], url_path=r"by-lesson/(?P<lesson_id>[^/.]+)"
    )
    def by_lesson(self, request, lesson_id=None):
        prg, _ = services.get_or_create_progress(user=request.user, lesson_id=lesson_id)
        return response.Response(ProgressSer(prg).data)

    @extend_schema(
        tags=["Progress"],
        summary="Mark lesson as complete",
        description="Manually marks a lesson as completed for the authenticated user.",
    )
    @decorators.action(
        detail=False, methods=["patch"], url_path=r"complete/(?P<lesson_id>[^/.]+)"
    )
    def complete(self, request, lesson_id=None):
        get_object_or_404(Lesson, id=lesson_id)
        prg = services.complete_lesson_for_user(user=request.user, lesson_id=lesson_id)
        return response.Response(ProgressSer(prg).data)


class LessonView(APIView):
    serializer_class = LessonSerializer

    def get_permissions(self):
        if self.request.method in ["PATCH", "PUT", "DELETE"]:
            return [IsTeacherOrReadOnly()]
        if self.request.method == "POST":
            return [IsAuthenticated()]
        return [AllowAny()]

    @extend_schema(
        tags=["Courses"],
        operation_id="v1_lesson_detail",
        responses={200: LessonLiteSer},
        summary="Retrieve lesson details",
        description="Returns the full content of a lesson, including the associated problem or quiz. Includes user-specific progress if authenticated.",
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
        tags=["Courses"],
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
        description="Processes a submission for a lesson. For JUDGE lessons, it evaluates code in a sandbox. For QUIZ lessons, it grades the provided answers. If the submission passes, the lesson is marked as completed.",
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

        # Ensure progress exists (mark as started)
        progress_obj, _ = services.get_or_create_progress(request.user, lesson.id)

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
        logger.info(f"Submission {sub.id} status: {sub.status}. Passed: {passed}")

        if passed:
            progress_obj = services.complete_lesson_for_user(request.user, lesson.id)

        next_url = self.get_next_url(lesson.course, lesson)

        return Response(
            {
                "passed": passed,
                "progress": ProgressLiteSer(progress_obj).data,
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

        # Ensure progress exists (mark as started)
        progress_obj, _ = services.get_or_create_progress(request.user, lesson.id)

        ser = AttemptSubmitSer(data=request.data)
        if not ser.is_valid():
            logger.error(f"Quiz validation failed: {ser.errors}. Data: {request.data}")
            return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)

        answers_data = ser.validated_data["answers"]

        # Fetch questions and choices
        quiz = lesson.quiz
        questions_map = {
            str(q.id): q for q in quiz.questions.prefetch_related("choices").all()
        }

        total_questions = len(questions_map)
        correct_count = 0

        # Create a map of user answers for easier lookup
        user_answers_map = {
            str(ans["question"]): str(ans["selected_choice_id"])
            for ans in answers_data
        }

        for q_id, question in questions_map.items():
            # Get the correct answer ID (there should be exactly one)
            correct_choice = question.choices.filter(is_answer=True).first()
            if not correct_choice:
                logger.warning(f"Question {q_id} in quiz {quiz.id} has no correct answer set.")
                continue

            correct_choice_id = str(correct_choice.id)
            user_selected_id = user_answers_map.get(q_id)

            # Check if user selection matches correct choice
            if user_selected_id and user_selected_id == correct_choice_id:
                correct_count += 1

        # Determine pass/fail (Require 100% correctness for now, or could use threshold)
        passed = (correct_count == total_questions) and (total_questions > 0)

        logger.info(
            f"Quiz for lesson {lesson.id} passed: {passed} ({correct_count}/{total_questions})"
        )

        if passed:
            progress_obj = services.complete_lesson_for_user(request.user, lesson.id)

        next_url = self.get_next_url(lesson.course, lesson)

        return Response(
            {
                "passed": passed,
                "progress": ProgressLiteSer(progress_obj).data,
                "next_url": next_url,
            },
            status=status.HTTP_201_CREATED,
        )
