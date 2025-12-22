import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")
django.setup()

from courses.models import Course, Lesson  # noqa: E402


def run():
    # Setup
    course, created = Course.objects.get_or_create(
        title="Test Course", slug="test-course"
    )
    Lesson.objects.filter(course=course).delete()

    print("Creating Lesson 1 (default order=0)...")
    l1 = Lesson(course=course, title="L1")  # order defaults to 0
    l1.save()
    print(f"L1: ID={l1.id}, Order={l1.order}, Slug={l1.slug}")

    print("Creating Lesson 2 (default order=0)...")
    l2 = Lesson(course=course, title="L2")
    l2.save()
    print(f"L2: ID={l2.id}, Order={l2.order}, Slug={l2.slug}")

    print("Creating Lesson 3 (explicit order=10)...")
    l3 = Lesson(course=course, title="L3", order=10)
    l3.save()
    print(f"L3: ID={l3.id}, Order={l3.order}, Slug={l3.slug}")

    print("Creating Lesson 4 (default order=0)...")
    # Max is 10. Should become 11.
    l4 = Lesson(course=course, title="L4")
    l4.save()
    print(f"L4: ID={l4.id}, Order={l4.order}, Slug={l4.slug}")


if __name__ == "__main__":
    run()
