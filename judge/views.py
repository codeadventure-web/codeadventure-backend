from django.shortcuts import get_object_or_404
from django.db import transaction
from rest_framework import viewsets, mixins, permissions, decorators, response, status
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly

from .models import Language, Problem, Submission
from .serializers import (
    LanguageSer,
    ProblemListSer,
    ProblemDetailSer,
    SubmitSer,
    SubmissionSer,
)
from .tasks import run_submission

# ========================
# Language ViewSet
# ========================
class LanguageViewSet(viewsets.ModelViewSet):
    """
    API cho Language:
    - Ai cũng được: GET list và retrieve
    - Chỉ user đã đăng nhập: POST, PUT, DELETE
    """
    queryset = Language.objects.all().order_by("key")
    serializer_class = LanguageSer
    permission_classes = [IsAuthenticatedOrReadOnly]


# ========================
# Problem ViewSet
# ========================
class ProblemViewSet(viewsets.ModelViewSet):
    queryset = Problem.objects.all().order_by("title")
    permission_classes = [IsAuthenticated]
    lookup_field = "slug"

    def get_serializer_class(self):
        if self.action in ["retrieve", "create", "update", "partial_update"]:
            return ProblemDetailSer
        return ProblemListSer

    @decorators.action(
        detail=True,
        methods=["post"],
        url_path="submit",
        permission_classes=[IsAuthenticated],
    )
    def submit(self, request, slug=None):
        problem = get_object_or_404(Problem, slug=slug)
        ser = SubmitSer(data=request.data)
        ser.is_valid(raise_exception=True)

        lang = get_object_or_404(Language, id=ser.validated_data["language_id"])

        if (
            problem.allowed_languages.exists()
            and not problem.allowed_languages.filter(id=lang.id).exists()
        ):
            raise ValidationError(
                {"language_id": ["This language is not allowed for this problem."]}
            )

        sub = Submission.objects.create(
            user=request.user,
            problem=problem,
            language=lang,
            code=ser.validated_data["code"],
        )

        transaction.on_commit(lambda: run_submission.delay(str(sub.id)))

        return response.Response(
            {"submission_id": str(sub.id), "status": sub.status},
            status=status.HTTP_201_CREATED
        )


# ========================
# Submission ViewSet
# ========================
class SubmissionViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet
):
    queryset = Submission.objects.all()
    serializer_class = SubmissionSer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)