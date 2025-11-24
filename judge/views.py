from django.shortcuts import get_object_or_404
from rest_framework import (
    viewsets,
    mixins,
    permissions,
    decorators,
    response,
    status,
)
from rest_framework.throttling import UserRateThrottle
from rest_framework.exceptions import ValidationError

from .models import Language, Problem, Submission
from .serializers import (
    LanguageSer,
    ProblemListSer,
    ProblemDetailSer,
    SubmitSer,
    SubmissionSer,
)
from common.permissions import IsAdminOrReadOnly, IsOwner
from .tasks import run_submission
from django.db import transaction


class SubmitThrottle(UserRateThrottle):
    scope = "submit"


class LanguageViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    queryset = Language.objects.all().order_by("key")
    serializer_class = LanguageSer
    permission_classes = [permissions.AllowAny]


class ProblemViewSet(viewsets.ModelViewSet):
    queryset = Problem.objects.all().order_by("title")
    permission_classes = [IsAdminOrReadOnly]
    lookup_field = "slug"

    def get_serializer_class(self):
        if self.action in ["retrieve", "create", "update", "partial_update"]:
            return ProblemDetailSer
        return ProblemListSer


class SubmissionViewSet(
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = SubmissionSer
    permission_classes = [permissions.IsAuthenticated, IsOwner]

    def get_queryset(self):
        return (
            Submission.objects.filter(user=self.request.user)
            .select_related("problem", "language")
            .order_by("-created_at")
        )

    @decorators.action(
        detail=False,
        methods=["post"],
        url_path=r"problems/(?P<slug>[^/.]+)/submit",
        throttle_classes=[SubmitThrottle],
        permission_classes=[permissions.IsAuthenticated],
    )
    def submit(self, request, slug=None):
        """
        POST /judge/submissions/problems/<slug>/submit/
        Body: { "language_id": "<uuid>", "code": "..." }
        """

        # 1. Problem + payload
        problem = get_object_or_404(Problem, slug=slug)
        ser = SubmitSer(data=request.data)
        ser.is_valid(raise_exception=True)

        # 2. Language
        lang = get_object_or_404(Language, id=ser.validated_data["language_id"])

        # 3. ENFORCE per-problem allowed languages
        # - If problem.allowed_languages is empty -> all languages allowed.
        # - Else, language must be in problem.allowed_languages.
        if (
            problem.allowed_languages.exists()
            and not problem.allowed_languages.filter(id=lang.id).exists()
        ):
            raise ValidationError(
                {"language_id": ["This language is not allowed for this problem."]}
            )

        # 4. Create submission
        sub = Submission.objects.create(
            user=request.user,
            problem=problem,
            language=lang,
            code=ser.validated_data["code"],
        )

        # 5. Enqueue async judge
        transaction.on_commit(lambda: run_submission.delay(str(sub.id)))

        # 6. Response
        return response.Response(
            {
                "submission_id": str(sub.id),
                "status": sub.status,
            },
            status=status.HTTP_202_ACCEPTED,
        )
