import logging
from .models import Progress
from accounts.models import User
from common.enums import ProgressStatus

logger = logging.getLogger(__name__)

# Lesson Progress Services


def get_or_create_progress(user: User, lesson_id: str) -> tuple[Progress, bool]:
    """
    Gets or creates a progress tracker for a user and a lesson.
    This now implicitly "starts" a course if it's the first lesson.

    Returns the (Progress, created) tuple.
    """
    return Progress.objects.get_or_create(
        user=user,
        lesson_id=lesson_id,
        defaults={"status": ProgressStatus.INCOMPLETE},
    )


def complete_lesson_for_user(user: User, lesson_id: str) -> Progress:
    """
    Marks a lesson as 'completed' for a user.
    """
    progress, _ = get_or_create_progress(user, lesson_id)

    if progress.status != ProgressStatus.COMPLETED:
        logger.info(f"Marking lesson {lesson_id} as COMPLETED for user {user.id}")
        progress.status = ProgressStatus.COMPLETED
        progress.save(update_fields=["status"])
    else:
        logger.info(f"Lesson {lesson_id} already COMPLETED for user {user.id}")

    return progress
