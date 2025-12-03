from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from .models import Course, Lesson, Progress
from common.enums import ProgressStatus  # Assuming this exists based on your imports

User = get_user_model()


class CourseProgressIsolationTests(APITestCase):
    def setUp(self):
        # 1. Setup Users
        self.alice = User.objects.create_user(username="alice", password="password123")
        self.bob = User.objects.create_user(username="bob", password="password123")

        # 2. Setup Course
        self.course = Course.objects.create(
            title="Advanced Python", slug="advanced-python", is_published=True
        )

        # 3. Setup Lessons
        self.lesson_1 = Lesson.objects.create(
            course=self.course, title="Intro to Decorators", order=1
        )
        self.lesson_2 = Lesson.objects.create(
            course=self.course, title="Generators", order=2
        )

        # 4. Setup Progress (The Critical Part)
        # Alice has completed Lesson 1 only
        Progress.objects.create(
            user=self.alice,
            lesson=self.lesson_1,
            status=ProgressStatus.COMPLETED,
            score=100.0,
        )

        # Bob has completed Lesson 2 only
        Progress.objects.create(
            user=self.bob,
            lesson=self.lesson_2,
            status=ProgressStatus.COMPLETED,
            score=85.0,
        )

        self.url = reverse("course-detail", kwargs={"slug": self.course.slug})

    def test_authenticated_user_sees_own_progress(self):
        """
        Verify that Alice sees Lesson 1 as COMPLETED and Lesson 2 as None/Incomplete.
        """
        self.client.force_authenticate(user=self.alice)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        lessons = response.data["lessons"]

        # Check Lesson 1 (Should be completed by Alice)
        l1_data = next(
            lesson_data
            for lesson_data in lessons
            if lesson_data["id"] == str(self.lesson_1.id)
        )
        self.assertIsNotNone(l1_data["progress"])
        self.assertEqual(l1_data["progress"]["status"], ProgressStatus.COMPLETED)
        self.assertEqual(l1_data["progress"]["score"], 100.0)

        # Check Lesson 2 (Alice has NOT started this, implies None or Incomplete)
        l2_data = next(
            lesson_data
            for lesson_data in lessons
            if lesson_data["id"] == str(self.lesson_2.id)
        )
        # Depending on serializer logic, this might be None or an empty object.
        # Based on your LessonLiteSer: "if progress: return ... return None"
        self.assertIsNone(l2_data["progress"])

    def test_data_isolation_between_users(self):
        """
        Verify that Bob DOES NOT see Alice's progress.
        Bob should see Lesson 1 as incomplete/None, and Lesson 2 as COMPLETED.
        """
        self.client.force_authenticate(user=self.bob)
        response = self.client.get(self.url)

        lessons = response.data["lessons"]

        # Check Lesson 1 (Bob has NOT touched this, but Alice has. Bob must see None)
        l1_data = next(
            lesson_data
            for lesson_data in lessons
            if lesson_data["id"] == str(self.lesson_1.id)
        )
        self.assertIsNone(
            l1_data["progress"], "Bob should not see Alice's progress on Lesson 1"
        )

        # Check Lesson 2 (Bob completed this)
        l2_data = next(
            lesson_data
            for lesson_data in lessons
            if lesson_data["id"] == str(self.lesson_2.id)
        )
        self.assertIsNotNone(l2_data["progress"])
        self.assertEqual(l2_data["progress"]["status"], ProgressStatus.COMPLETED)
        self.assertEqual(l2_data["progress"]["score"], 85.0)

    def test_anonymous_user_sees_no_progress(self):
        """
        Verify that unauthenticated users see the course content but NO progress data.
        """
        self.client.logout()
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        lessons = response.data["lessons"]

        # All progress fields should be None
        for lesson in lessons:
            self.assertIsNone(lesson["progress"])
