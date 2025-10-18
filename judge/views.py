from rest_framework import viewsets, mixins, permissions, decorators, response, status
from rest_framework.throttling import UserRateThrottle
from django.shortcuts import get_object_or_404
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


class SubmitThrottle(UserRateThrottle):
    scope = "submit"


@decorators.action(
    detail=False,
    methods=["post"],
    url_path=r"problems/(?P<slug>[^/.]+)/submit",
    throttle_classes=[SubmitThrottle],
)
def submit(self, request, slug=None): ...


class LanguageViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    queryset = Language.objects.all().order_by("key")
    serializer_class = LanguageSer
    permission_classes = [permissions.AllowAny]


class ProblemViewSet(viewsets.ModelViewSet):
    queryset = Problem.objects.all().order_by("title")
    permission_classes = [IsAdminOrReadOnly]
    lookup_field = "slug"

    def get_serializer_class(self):
        return (
            ProblemDetailSer
            if self.action in ["retrieve", "create", "update", "partial_update"]
            else ProblemListSer
        )


class SubmissionViewSet(
    mixins.RetrieveModelMixin, mixins.ListModelMixin, viewsets.GenericViewSet
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
        detail=False, methods=["post"], url_path=r"problems/(?P<slug>[^/.]+)/submit"
    )
    def submit(self, request, slug=None):
        problem = get_object_or_404(Problem, slug=slug)
        ser = SubmitSer(data=request.data)
        ser.is_valid(raise_exception=True)
        lang = get_object_or_404(Language, id=ser.validated_data["language_id"])
        sub = Submission.objects.create(
            user=request.user,
            problem=problem,
            language=lang,
            code=ser.validated_data["code"],
        )
        run_submission.delay(str(sub.id))
        return response.Response(
            {"submission_id": str(sub.id)}, status=status.HTTP_202_ACCEPTED
        )
