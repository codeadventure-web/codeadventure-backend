import pytest


@pytest.mark.django_db
def test_lesson_detail_slug_url(api_client, course_python, lesson_decorators):
    # The new URL should be /api/v1/<course_slug>/<lesson_slug>/
    url = f"/api/v1/{course_python.slug}/{lesson_decorators.slug}/"
    resp = api_client.get(url)

    assert resp.status_code == 200
    assert resp.data["title"] == lesson_decorators.title
    assert resp.data["slug"] == lesson_decorators.slug


@pytest.mark.django_db
def test_lesson_detail_invalid_slugs(api_client, course_python):
    url = f"/api/v1/{course_python.slug}/invalid-lesson-slug/"
    resp = api_client.get(url)
    assert resp.status_code == 404

    url = "/api/v1/invalid-course-slug/some-lesson/"
    resp = api_client.get(url)
    assert resp.status_code == 404
