import pytest


@pytest.mark.django_db
def test_health_ok(monkeypatch, api_client):
    # patch redis.from_url
    class FakeRedis:
        def ping(self): ...

    import accounts.views as accounts_views

    monkeypatch.setattr(accounts_views.redis, "from_url", lambda *a, **k: FakeRedis())

    resp = api_client.get("/api/v1/health/")
    assert resp.status_code == 200
    assert resp.data["status"] in ("ok", "degraded")
    # at least both keys present
    assert "db" in resp.data
    assert "redis" in resp.data
