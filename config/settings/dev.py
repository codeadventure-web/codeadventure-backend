from .base import *  # noqa: F403, F405

DEBUG = True
ALLOWED_HOSTS = ["*"]
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

CORS_ALLOW_ALL_ORIGINS = True
