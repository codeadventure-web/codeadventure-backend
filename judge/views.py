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
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly

from .models import Language, Problem, Submission
from .serializers import (
    LanguageSer,
    ProblemListSer,
    ProblemDetailSer,
    SubmitSer,
    SubmissionSer,
)
from common.permissions import IsOwner  
from .tasks import run_submission
from django.db import transaction


# ========================
# Language ViewSet
# ========================
class LanguageViewSet(viewsets.ModelViewSet):
    """
    API cho Language:
    - Ai cũng được: GET list và retrieve
    - Chỉ user đã đăng nhập: POST (tạo), PUT/PATCH (sửa), DELETE (xóa)
    """
    queryset = Language.objects.all().order_by("key")
    serializer_class = LanguageSer
    permission_classes = [IsAuthenticatedOrReadOnly]  


# ========================
# Problem ViewSet
# ========================
class ProblemViewSet(viewsets.ModelViewSet):
    queryset = Problem.objects.all().order_by("title")
    permission_classes = [IsAuthenticated]  # Giữ nguyên: chỉ user đăng nhập mới quản lý problem
    lookup_field = "slug"

    def get_serializer_class(self):
        if self.action in ["retrieve", "create", "update", "partial_update"]:
            return ProblemDetailSer
        return ProblemListSer


# ========================
# Submission ViewSet
# ========================
class SubmitThrottle(UserRateThrottle):
    scope = "submit"


class SubmissionViewSet(
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = SubmissionSer
    permission_classes = [IsAuthenticated, IsOwner]

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
        permission_classes=[IsAuthenticated],
    )
    def submit(self, request, slug=None):
        """
        POST /judge/submissions/problems/<slug>/submit/
        Body: { "language_id": "<uuid>", "code": "..." }
        """
        # 1. Lấy problem
        problem = get_object_or_404(Problem, slug=slug)

        # 2. Validate payload
        ser = SubmitSer(data=request.data)
        ser.is_valid(raise_exception=True)

        # 3. Lấy language
        lang = get_object_or_404(Language, id=ser.validated_data["language_id"])

        # 4. Kiểm tra ngôn ngữ có được phép cho problem này không
        if (
            problem.allowed_languages.exists()
            and not problem.allowed_languages.filter(id=lang.id).exists()
        ):
            raise ValidationError(
                {"language_id": ["This language is not allowed for this problem."]}
            )

        # 5. Tạo submission
        sub = Submission.objects.create(
            user=request.user,
            problem=problem,
            language=lang,
            code=ser.validated_data["code"],
        )

        # 6. Đẩy vào queue Celery
        transaction.on_commit(lambda: run_submission.delay(str(sub.id)))

        # 7. Trả response
        return response.Response(
            {
                "submission_id": str(sub.id),
                "status": sub.status,
            },
            status=status.HTTP_202_ACCEPTED,
        )