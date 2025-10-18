from django.core.management.base import BaseCommand
from judge.models import Language, Problem, TestCase


class Command(BaseCommand):
    help = "Seed demo data"

    def handle(self, *args, **kwargs):
        Language.objects.get_or_create(key="python", defaults={"version": "3.11"})
        Language.objects.get_or_create(key="cpp", defaults={"version": "GCC 13"})
        p, _ = Problem.objects.get_or_create(
            slug="sum-two",
            defaults={
                "title": "Sum Two Numbers",
                "statement_md": "Read two ints a,b and print a+b.",
                "time_limit_ms": 2000,
                "memory_limit_mb": 256,
            },
        )
        TestCase.objects.get_or_create(
            problem=p, input_data="1 2\n", expected_output="3\n", hidden=False
        )
        TestCase.objects.get_or_create(
            problem=p, input_data="10 20\n", expected_output="30\n", hidden=True
        )
        self.stdout.write(self.style.SUCCESS("Seeded."))
