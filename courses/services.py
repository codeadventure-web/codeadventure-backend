from .models import Progress
from accounts.models import User


# Lesson Progress Services


def get_or_create_progress(user: User, lesson_id: str) -> tuple[Progress, bool]:
    """
    Gets or creates a progress tracker for a user and a lesson.
    This now implicitly "starts" a course if it's the first lesson.

    Returns the (Progress, created) tuple.
    """
    return Progress.objects.get_or_create(user=user, lesson_id=lesson_id)


def complete_lesson_for_user(user: User, lesson_id: str) -> Progress:
    """
    Marks a lesson as 'completed' for a user.
    """
    progress, _ = get_or_create_progress(user, lesson_id)

    if progress.status != "completed":
        progress.status = "completed"
        progress.save(update_fields=["status"])

    return progress
