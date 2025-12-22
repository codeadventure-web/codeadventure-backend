import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")
django.setup()

from courses.models import Course, Lesson


def run():
    # Setup
    course, created = Course.objects.get_or_create(
        title="Inline Test Course", slug="inline-test"
    )
    Lesson.objects.filter(course=course).delete()

    print("Simulating Inline: Adding multiple lessons...")
    # Inlines are saved one by one, but usually in a transaction.
    # The form defaults 'order' to 0 for all new rows if not filled.

    l1 = Lesson(course=course, title="Inline 1", order=0)
    l1.save()
    print(f"L1: Order={l1.order}, Slug={l1.slug}")

    l2 = Lesson(course=course, title="Inline 2", order=0)
    l2.save()
    print(f"L2: Order={l2.order}, Slug={l2.slug}")

    l3 = Lesson(course=course, title="Inline 3", order=0)
    l3.save()
    print(f"L3: Order={l3.order}, Slug={l3.slug}")


if __name__ == "__main__":
    run()
