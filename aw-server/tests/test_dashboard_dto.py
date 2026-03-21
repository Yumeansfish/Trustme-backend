import json
from pathlib import Path
from datetime import datetime, timedelta, timezone

from aw_server.dashboard_dto import (
    serialize_dashboard_details_response,
    serialize_dashboard_default_hosts_response,
    serialize_dashboard_scope_response,
    serialize_checkins_response,
    serialize_summary_snapshot_response,
)
from aw_server.settings_schema import normalize_settings_data
from aw_server.server import AWFlask


FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures" / "dashboard"


def load_dashboard_fixture(name: str):
    with open(FIXTURE_DIR / name) as handle:
        return json.load(handle)


def test_serialize_summary_snapshot_response_normalizes_shape_and_backfills_periods():
    category_periods = [
        "2026-03-01T10:00:00+00:00/2026-03-01T11:00:00+00:00",
        "2026-03-01T11:00:00+00:00/2026-03-01T12:00:00+00:00",
    ]

    payload = {
        "window": {
            "app_events": [
                {
                    "timestamp": "2026-03-01T10:00:00+00:00",
                    "duration": "1800",
                    "data": {"app": "Code"},
                }
            ],
            "duration": "3600",
        },
        "by_period": {
            category_periods[0]: {
                "cat_events": [
                    {
                        "timestamp": "2026-03-01T10:00:00+00:00",
                        "duration": "1800",
                        "data": {"$category": ["Code"]},
                    }
                ]
            }
        },
        "uncategorized_rows": [{"app": "Antigravity", "duration": "900"}],
    }

    result = serialize_summary_snapshot_response(payload, category_periods=category_periods)

    assert result["window"]["duration"] == 3600.0
    assert result["window"]["app_events"][0]["duration"] == 1800.0
    assert result["window"]["title_events"] == []
    assert result["window"]["active_events"] == []
    assert list(result["by_period"].keys()) == category_periods
    assert result["by_period"][category_periods[1]] == {"cat_events": []}
    assert result["uncategorized_rows"] == [
        {
            "key": "Antigravity",
            "app": "Antigravity",
            "title": "Antigravity",
            "subtitle": "",
            "duration": 900.0,
            "matchText": "Antigravity",
        }
    ]


def test_serialize_checkins_response_derives_counts_and_normalizes_values():
    payload = {
        "available_dates": ["2026-03-14"],
        "sessions": [
            {
                "id": 12,
                "date": "2026-03-14",
                "answers": [
                    {
                        "question_id": 1,
                        "emoji": "🙂",
                        "label": "Mood",
                        "status": "answered",
                        "value": "4",
                        "value_label": "4/5",
                        "progress": "80",
                    },
                    {
                        "question_id": "2",
                        "status": "skipped",
                    },
                ],
            }
        ],
    }

    result = serialize_checkins_response(payload)

    assert result["data_source"] == ""
    assert result["available_dates"] == ["2026-03-14"]
    session = result["sessions"][0]
    assert session["id"] == "12"
    assert session["answered_count"] == 1
    assert session["skipped_count"] == 1
    assert session["duration_seconds"] == 0
    assert session["answers"][0]["value"] == 4
    assert session["answers"][0]["progress"] == 80.0
    assert session["answers"][1]["value"] is None


def test_serialize_dashboard_scope_response_normalizes_lists():
    payload = {
        "requested_hosts": ["alpha.local", 12],
        "resolved_hosts": ["alpha.local"],
        "window_buckets": ["window-a"],
        "afk_buckets": None,
        "browser_buckets": ["browser-a"],
        "stopwatch_buckets": ["stopwatch-a", "stopwatch-b"],
    }

    result = serialize_dashboard_scope_response(payload)

    assert result == {
        "requested_hosts": ["alpha.local", "12"],
        "resolved_hosts": ["alpha.local"],
        "window_buckets": ["window-a"],
        "afk_buckets": [],
        "browser_buckets": ["browser-a"],
        "stopwatch_buckets": ["stopwatch-a", "stopwatch-b"],
    }


def test_serialize_dashboard_default_hosts_response_normalizes_lists():
    result = serialize_dashboard_default_hosts_response({"resolved_hosts": ["alpha.local", 12]})

    assert result == {
        "resolved_hosts": ["alpha.local", "12"],
    }


def test_dashboard_contract_summary_fixtures_roundtrip_stable_shapes():
    for fixture_name in (
        "dashboard-summary-empty.json",
        "dashboard-summary-single-device.json",
        "dashboard-summary-grouped-multidevice.json",
    ):
        fixture = load_dashboard_fixture(fixture_name)
        assert serialize_summary_snapshot_response(
            fixture,
            category_periods=list(fixture["by_period"].keys()),
        ) == fixture


def test_dashboard_contract_detail_scope_and_checkin_fixtures_roundtrip_stable_shapes():
    details_fixture = load_dashboard_fixture("dashboard-details-browser-stopwatch.json")
    scope_fixture = load_dashboard_fixture("dashboard-scope-grouped-multidevice.json")
    default_hosts_fixture = load_dashboard_fixture("dashboard-default-hosts.json")
    checkins_fixture = load_dashboard_fixture("dashboard-checkins.json")

    assert serialize_dashboard_details_response(details_fixture) == details_fixture
    assert serialize_dashboard_scope_response(scope_fixture) == scope_fixture
    assert serialize_dashboard_default_hosts_response(default_hosts_fixture) == default_hosts_fixture
    assert serialize_checkins_response(checkins_fixture) == checkins_fixture


def test_dashboard_settings_fixture_matches_backend_normalization():
    normalized_fixture = load_dashboard_fixture("dashboard-settings-normalized.json")
    raw_settings = {
        "startOfDay": "09:00",
        "startOfWeek": "Monday",
        "landingpage": "/activity",
        "theme": "dark",
        "alwaysActivePattern": "Zoom|Teams",
        "classes": [
            {
                "name": ["Work", "Coding"],
                "rule": {
                    "type": "regex",
                    "regex": "Code",
                    "ignore_case": True,
                },
            }
        ],
        "categorizationKnowledgebaseVersion": 1,
        "devmode": False,
        "showYearly": False,
        "useMultidevice": False,
        "requestTimeout": 30,
        "deviceMappings": {
            "Office": ["alpha.local", "beta.local"],
        },
    }

    normalized, changed = normalize_settings_data(raw_settings)

    assert changed is True
    assert normalized == normalized_fixture


def test_serialize_dashboard_details_response_normalizes_nested_shapes():
    payload = {
        "browser": {
            "domains": [{"timestamp": "2026-03-01T10:00:00+00:00", "duration": "600", "data": {"$domain": "example.com"}}],
            "duration": "600",
        },
        "stopwatch": {
            "stopwatch_events": [
                {"timestamp": "2026-03-01T10:00:00+00:00", "duration": "300", "data": {"label": "Break"}}
            ]
        },
    }

    result = serialize_dashboard_details_response(payload)

    assert result["browser"]["domains"][0]["duration"] == 600.0
    assert result["browser"]["urls"] == []
    assert result["stopwatch"]["stopwatch_events"][0]["data"]["label"] == "Break"


def test_server_api_summary_snapshot_serializes_builder_output(monkeypatch):
    app = AWFlask("127.0.0.1", testing=True)
    base = datetime(2026, 3, 1, 10, 0, tzinfo=timezone.utc)
    category_period = f"{base.isoformat()}/{(base + timedelta(hours=1)).isoformat()}"
    captured_kwargs = {}

    def fake_summary_snapshot(**kwargs):
        captured_kwargs.update(kwargs)
        return {
            "window": {
                "app_events": [],
                "title_events": [],
                "cat_events": [],
                "active_events": [],
                "duration": 1800.0,
            },
            "by_period": {category_period: {"cat_events": []}},
            "uncategorized_rows": [
                {
                    "key": "Antigravity",
                    "app": "Antigravity",
                    "title": "Antigravity",
                    "subtitle": "",
                    "duration": 0.0,
                    "matchText": "Antigravity",
                }
            ],
        }

    monkeypatch.setattr(app.api.dashboard, "summary_snapshot", fake_summary_snapshot)

    result = app.api.summary_snapshot(
        range_start=base,
        range_end=base + timedelta(hours=1),
        category_periods=[category_period],
        window_buckets=["test-window"],
        afk_buckets=["test-afk"],
        stopwatch_buckets=[],
        filter_afk=True,
        filter_categories=[],
    )

    assert captured_kwargs["window_buckets"] == ["test-window"]
    assert captured_kwargs["category_periods"] == [category_period]
    assert result["window"]["duration"] == 1800.0
    assert result["window"]["app_events"] == []
    assert result["by_period"][category_period] == {"cat_events": []}
    assert result["uncategorized_rows"][0]["title"] == "Antigravity"


def test_server_api_get_checkins_delegates_to_dashboard_facade(monkeypatch):
    app = AWFlask("127.0.0.1", testing=True)

    def fake_checkins(*, date_filter=None):
        assert date_filter == "2026-03-14"
        return {
            "data_source": "",
            "available_dates": ["2026-03-14"],
            "sessions": [{"id": "session-1", "answers": [{"status": "answered"}]}],
        }

    monkeypatch.setattr(app.api.dashboard, "checkins", fake_checkins)

    result = app.api.get_checkins(date_filter="2026-03-14")

    assert result["data_source"] == ""
    assert result["available_dates"] == ["2026-03-14"]
    assert result["sessions"][0]["id"] == "session-1"


def test_server_api_resolve_dashboard_scope_serializes_builder_output(monkeypatch):
    app = AWFlask("127.0.0.1", testing=True)
    base = datetime(2026, 3, 1, 10, 0, tzinfo=timezone.utc)

    def fake_resolve_scope(**kwargs):
        assert kwargs["requested_hosts"] == ["alpha.local"]
        assert kwargs["range_start"] == base
        assert kwargs["range_end"] == base + timedelta(hours=1)
        return {
            "requested_hosts": ["alpha.local"],
            "resolved_hosts": ["alpha.local", "beta.local"],
            "window_buckets": ["window-a"],
            "afk_buckets": ["afk-a"],
            "browser_buckets": ["browser-a"],
            "stopwatch_buckets": ["stopwatch-a"],
        }

    monkeypatch.setattr(app.api.dashboard, "resolve_scope", fake_resolve_scope)

    result = app.api.resolve_dashboard_scope(
        requested_hosts=["alpha.local"],
        range_start=base,
        range_end=base + timedelta(hours=1),
    )

    assert result["requested_hosts"] == ["alpha.local"]
    assert result["resolved_hosts"] == ["alpha.local", "beta.local"]
    assert result["window_buckets"] == ["window-a"]
    assert result["browser_buckets"] == ["browser-a"]


def test_server_api_dashboard_details_serializes_builder_output(monkeypatch):
    app = AWFlask("127.0.0.1", testing=True)
    base = datetime(2026, 3, 1, 10, 0, tzinfo=timezone.utc)

    def fake_details(**kwargs):
        assert kwargs["window_buckets"] == ["window-a"]
        assert kwargs["browser_buckets"] == ["browser-a"]
        assert kwargs["stopwatch_buckets"] == ["stopwatch-a"]
        return {
            "browser": {
                "domains": [
                    {
                        "timestamp": base.isoformat(),
                        "duration": "600",
                        "data": {"$domain": "example.com"},
                    }
                ],
                "duration": "600",
            },
            "stopwatch": {
                "stopwatch_events": [
                    {
                        "timestamp": base.isoformat(),
                        "duration": "300",
                        "data": {"label": "Break"},
                    }
                ]
            },
        }

    monkeypatch.setattr(app.api.dashboard, "details", fake_details)

    result = app.api.dashboard_details(
        range_start=base,
        range_end=base + timedelta(hours=1),
        window_buckets=["window-a"],
        browser_buckets=["browser-a"],
        stopwatch_buckets=["stopwatch-a"],
    )

    assert result["browser"]["domains"][0]["data"]["$domain"] == "example.com"
    assert result["stopwatch"]["stopwatch_events"][0]["data"]["label"] == "Break"


def test_server_api_default_dashboard_hosts_serializes_builder_output(monkeypatch):
    app = AWFlask("127.0.0.1", testing=True)

    def fake_default_hosts():
        return {"resolved_hosts": ["alpha.local", "beta.local"]}

    monkeypatch.setattr(app.api.dashboard, "default_hosts", fake_default_hosts)

    result = app.api.default_dashboard_hosts()

    assert result == {"resolved_hosts": ["alpha.local", "beta.local"]}
