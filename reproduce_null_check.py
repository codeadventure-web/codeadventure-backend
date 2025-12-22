import os
import django
from django.core.exceptions import ValidationError

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")
django.setup()

from courses.models import Course, Lesson  # noqa: E402


def run():
    course, _ = Course.objects.get_or_create(
        title="Null Slug Test", slug="null-slug-test"
    )
    Lesson.objects.filter(course=course).delete()

    print("Creating two unsaved lessons with slug=None...")
    # Simulate what Admin does when slug is missing and default is None
    l1 = Lesson(course=course, title="L1", order=0)  # slug defaults to None
    l2 = Lesson(course=course, title="L2", order=0)  # slug defaults to None

    print(f"L1 slug: {l1.slug}")
    print(f"L2 slug: {l2.slug}")

    try:
        print("Validating L1...")
        l1.validate_unique()
        print("L1 valid.")
    except ValidationError as e:
        print(f"L1 invalid: {e}")

    try:
        print("Validating L2...")
        l2.validate_unique()
        print("L2 valid.")
    except ValidationError as e:
        print(f"L2 invalid: {e}")

    # Note: validate_unique() checks against DATABASE.
    # Since neither is in DB, they don't conflict with DB.
    # But do they conflict with each other?
    # validate_unique doesn't know about other in-memory instances.
    # The Admin FormSet validation does.

    # However, verifying that we can have multiple saved lessons with slug=None (if we wanted)
    # would prove DB accepts it, but we enforce slug setting on save.

    print("Saving L1...")
    l1.save()
    print(f"L1 Saved: {l1.slug}")

    print("Saving L2...")
    l2.save()
    print(f"L2 Saved: {l2.slug}")


if __name__ == "__main__":
    run()
