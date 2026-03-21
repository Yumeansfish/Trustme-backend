from datetime import datetime, timedelta, timezone

from aw_server.server import AWFlask


def test_summary_snapshot_route():
    app = AWFlask("127.0.0.1", testing=True)
    flask_client = app.test_client()
    base = datetime(2026, 3, 1, 10, 0, tzinfo=timezone.utc)
    category_periods = [
        f"{base.isoformat()}/{(base + timedelta(minutes=30)).isoformat()}",
    ]
    expected = {
        "window": {
            "app_events": [],
            "title_events": [],
            "cat_events": [],
            "active_events": [],
            "duration": 0,
        },
        "by_period": {category_periods[0]: {"cat_events": []}},
        "uncategorized_rows": [],
    }
    captured = {}

    def fake_summary_snapshot(**kwargs):
        captured.update(kwargs)
        return expected

    app.api.summary_snapshot = fake_summary_snapshot

    payload = {
        "range": {
            "start": base.isoformat(),
            "end": (base + timedelta(hours=1)).isoformat(),
        },
        "category_periods": category_periods,
        "window_buckets": ["test-window"],
        "afk_buckets": ["test-afk"],
        "stopwatch_buckets": [],
        "filter_afk": True,
        "filter_categories": [],
    }

    r = flask_client.post("/api/0/dashboard/summary-snapshot", json=payload)
    assert r.status_code == 200
    assert r.json == expected
    assert captured["range_start"] == base
    assert captured["range_end"] == base + timedelta(hours=1)
    assert captured["category_periods"] == category_periods
    assert captured["window_buckets"] == ["test-window"]
    assert captured["categories"] is None
    assert captured["always_active_pattern"] is None


def test_dashboard_scope_route():
    app = AWFlask("127.0.0.1", testing=True)
    flask_client = app.test_client()
    base = datetime(2026, 3, 1, 10, 0, tzinfo=timezone.utc)
    expected = {
        "requested_hosts": ["alpha.local"],
        "resolved_hosts": ["alpha.local", "beta.local"],
        "window_buckets": ["window-a"],
        "afk_buckets": ["afk-a"],
        "browser_buckets": ["browser-a"],
        "stopwatch_buckets": ["stopwatch-a"],
    }
    captured = {}

    def fake_resolve_dashboard_scope(**kwargs):
        captured.update(kwargs)
        return expected

    app.api.resolve_dashboard_scope = fake_resolve_dashboard_scope

    payload = {
        "hosts": ["alpha.local"],
        "range": {
            "start": base.isoformat(),
            "end": (base + timedelta(hours=1)).isoformat(),
        },
    }

    r = flask_client.post("/api/0/dashboard/resolve-scope", json=payload)
    assert r.status_code == 200
    assert r.json == expected
    assert captured["requested_hosts"] == ["alpha.local"]
    assert captured["range_start"] == base
    assert captured["range_end"] == base + timedelta(hours=1)


def test_dashboard_details_route():
    app = AWFlask("127.0.0.1", testing=True)
    flask_client = app.test_client()
    base = datetime(2026, 3, 1, 10, 0, tzinfo=timezone.utc)
    expected = {
        "browser": {"domains": [], "urls": [], "titles": [], "duration": 0},
        "stopwatch": {"stopwatch_events": []},
    }
    captured = {}

    def fake_dashboard_details(**kwargs):
        captured.update(kwargs)
        return expected

    app.api.dashboard_details = fake_dashboard_details

    payload = {
        "range": {
            "start": base.isoformat(),
            "end": (base + timedelta(hours=1)).isoformat(),
        },
        "window_buckets": ["window-a"],
        "browser_buckets": ["browser-a"],
        "stopwatch_buckets": ["stopwatch-a"],
    }

    r = flask_client.post("/api/0/dashboard/details", json=payload)
    assert r.status_code == 200
    assert r.json == expected
    assert captured["window_buckets"] == ["window-a"]
    assert captured["browser_buckets"] == ["browser-a"]
    assert captured["stopwatch_buckets"] == ["stopwatch-a"]


def test_default_dashboard_hosts_route():
    app = AWFlask("127.0.0.1", testing=True)
    flask_client = app.test_client()

    app.api.default_dashboard_hosts = lambda: {"resolved_hosts": ["alpha.local", "beta.local"]}

    r = flask_client.get("/api/0/dashboard/default-hosts")
    assert r.status_code == 200
    assert r.json == {"resolved_hosts": ["alpha.local", "beta.local"]}
