from datetime import datetime, timedelta, timezone

import aw_server.dashboard_api_facade as dashboard_api_facade_module
from aw_server.server import AWFlask


def test_dashboard_facade_summary_snapshot_uses_settings_and_store(monkeypatch):
    app = AWFlask("127.0.0.1", testing=True)
    base = datetime(2026, 3, 1, 10, 0, tzinfo=timezone.utc)
    category_period = f"{base.isoformat()}/{(base + timedelta(minutes=30)).isoformat()}"
    captured_kwargs = {}

    def fake_build_summary_snapshot_response(**kwargs):
        captured_kwargs.update(kwargs)
        return {
            "window": {
                "app_events": [],
                "title_events": [],
                "cat_events": [],
                "active_events": [],
                "duration": 0,
            },
            "by_period": {category_period: {"cat_events": []}},
            "uncategorized_rows": [],
        }

    monkeypatch.setattr(
        dashboard_api_facade_module,
        "build_summary_snapshot_response",
        fake_build_summary_snapshot_response,
    )

    result = app.api.dashboard.summary_snapshot(
        range_start=base,
        range_end=base + timedelta(hours=1),
        category_periods=[category_period],
        window_buckets=["test-window"],
        afk_buckets=["test-afk"],
        stopwatch_buckets=[],
        filter_afk=True,
        filter_categories=[],
    )

    assert captured_kwargs["settings_data"] == app.api.settings.get("")
    assert captured_kwargs["summary_snapshot_store"] == app.api.summary_snapshot_store
    assert captured_kwargs["window_buckets"] == ["test-window"]
    assert result["by_period"][category_period] == {"cat_events": []}


def test_dashboard_facade_checkins_returns_builder_payload(monkeypatch):
    app = AWFlask("127.0.0.1", testing=True)

    def fake_build_checkins_payload(*, date_filter=None):
        assert date_filter == "2026-03-14"
        return {
            "data_source": "",
            "available_dates": ["2026-03-14"],
            "sessions": [{"id": "session-1", "answers": [{"status": "answered"}]}],
        }

    monkeypatch.setattr(
        dashboard_api_facade_module,
        "build_checkins_payload",
        fake_build_checkins_payload,
    )

    result = app.api.dashboard.checkins(date_filter="2026-03-14")

    assert result["available_dates"] == ["2026-03-14"]
    assert result["sessions"][0]["answers"][0]["status"] == "answered"


def test_dashboard_facade_resolve_scope_builds_bucket_records(monkeypatch):
    app = AWFlask("127.0.0.1", testing=True)
    base = datetime(2026, 3, 1, 10, 0, tzinfo=timezone.utc)
    captured_kwargs = {}

    def fake_build_dashboard_scope_response(**kwargs):
        captured_kwargs.update(kwargs)
        return {
            "requested_hosts": ["alpha.local"],
            "resolved_hosts": ["alpha.local"],
            "window_buckets": [],
            "afk_buckets": [],
            "browser_buckets": [],
            "stopwatch_buckets": [],
        }

    monkeypatch.setattr(
        dashboard_api_facade_module,
        "build_dashboard_scope_response",
        fake_build_dashboard_scope_response,
    )

    result = app.api.dashboard.resolve_scope(
        requested_hosts=["alpha.local"],
        range_start=base,
        range_end=base + timedelta(hours=1),
    )

    assert captured_kwargs["settings_data"] == app.api.settings.get("")
    assert isinstance(captured_kwargs["bucket_records"], list)
    assert result["requested_hosts"] == ["alpha.local"]


def test_dashboard_facade_details_delegates_to_builder(monkeypatch):
    app = AWFlask("127.0.0.1", testing=True)
    base = datetime(2026, 3, 1, 10, 0, tzinfo=timezone.utc)
    captured_kwargs = {}

    def fake_build_dashboard_details_response(**kwargs):
        captured_kwargs.update(kwargs)
        return {
            "browser": {"domains": [], "urls": [], "titles": [], "duration": 0},
            "stopwatch": {"stopwatch_events": []},
        }

    monkeypatch.setattr(
        dashboard_api_facade_module,
        "build_dashboard_details_response",
        fake_build_dashboard_details_response,
    )

    result = app.api.dashboard.details(
        range_start=base,
        range_end=base + timedelta(hours=1),
        window_buckets=["window-a"],
        browser_buckets=["browser-a"],
        stopwatch_buckets=["stopwatch-a"],
    )

    assert captured_kwargs["window_buckets"] == ["window-a"]
    assert captured_kwargs["browser_buckets"] == ["browser-a"]
    assert result["stopwatch"]["stopwatch_events"] == []


def test_dashboard_facade_default_hosts_builds_bucket_records(monkeypatch):
    app = AWFlask("127.0.0.1", testing=True)
    captured_kwargs = {}

    def fake_build_default_dashboard_hosts_response(**kwargs):
        captured_kwargs.update(kwargs)
        return {"resolved_hosts": ["alpha.local", "beta.local"]}

    monkeypatch.setattr(
        dashboard_api_facade_module,
        "build_default_dashboard_hosts_response",
        fake_build_default_dashboard_hosts_response,
    )

    result = app.api.dashboard.default_hosts()

    assert captured_kwargs["settings_data"] == app.api.settings.get("")
    assert isinstance(captured_kwargs["bucket_records"], list)
    assert result == {"resolved_hosts": ["alpha.local", "beta.local"]}
