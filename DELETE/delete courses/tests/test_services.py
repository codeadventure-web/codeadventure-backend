import pytest
from courses import services
from common.enums import ProgressStatus


@pytest.mark.django_db
def test_get_or_create_progress(user_alice, lesson_decorators):
    # 1. Create new
    progress, created = services.get_or_create_progress(
        user_alice, lesson_decorators.id
    )
    assert created is True
    assert progress.status == ProgressStatus.INCOMPLETE

    # 2. Get existing
    progress2, created2 = services.get_or_create_progress(
        user_alice, lesson_decorators.id
    )
    assert created2 is False
    assert progress2.id == progress.id


@pytest.mark.django_db
def test_complete_lesson_for_user(user_alice, lesson_decorators):
    progress = services.complete_lesson_for_user(user_alice, lesson_decorators.id)

    assert progress.status == ProgressStatus.COMPLETED
    assert progress.user == user_alice
    assert progress.lesson == lesson_decorators
