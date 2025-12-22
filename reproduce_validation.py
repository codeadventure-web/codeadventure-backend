import os
import django
from django.core.exceptions import ValidationError

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")
django.setup()

from courses.models import Course, Lesson

def run():
    course, _ = Course.objects.get_or_create(title="Validation Test", slug="valid-test")
    Lesson.objects.filter(course=course).delete()

    print("Creating two unsaved lessons with empty slug...")
    l1 = Lesson(course=course, title="L1", order=0, slug="")
    l2 = Lesson(course=course, title="L2", order=0, slug="")
    
    # Simulate Formset validation
    try:
        print("Validating L1...")
        l1.validate_unique()
        print("L1 valid.")
    except ValidationError as e:
        print(f"L1 invalid: {e}")

    # L1 is not saved yet.
    
    try:
        print("Validating L2...")
        l2.validate_unique()
        print("L2 valid.")
    except ValidationError as e:
        print(f"L2 invalid: {e}")

    # If I save L1, then validate L2?
    print("Saving L1...")
    l1.save() # slug becomes "01"
    print(f"L1 saved. Slug: {l1.slug}")

    try:
        print("Validating L2 (after L1 saved)...")
        l2.validate_unique()
        print("L2 valid.")
    except ValidationError as e:
        print(f"L2 invalid: {e}")
        
    print("Saving L2...")
    l2.save() # slug becomes "02"
    print(f"L2 saved. Slug: {l2.slug}")

if __name__ == "__main__":
    run()
