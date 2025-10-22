import random
import string
from django.utils.text import slugify


def generate_random_string(length=8):
    """Generates a random string of fixed length."""
    letters = string.ascii_lowercase + string.digits
    return "".join(random.choice(letters) for i in range(length))


def generate_unique_slug(model_class, title):
    """
    Generates a unique slug for a given model and title.
    If a slug already exists, it appends a random string.
    """
    slug = slugify(title)
    base_slug = slug

    # Check if a slug already exists
    while model_class.objects.filter(slug=slug).exists():
        # Append a random string to make it unique
        random_str = generate_random_string(length=4)
        slug = f"{base_slug}-{random_str}"

    return slug
