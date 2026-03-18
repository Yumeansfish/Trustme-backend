from datetime import datetime, timedelta, timezone

import aw_server.api as api_module
from aw_server.dashboard_dto import (
    serialize_checkins_response,
    serialize_summary_snapshot_response,
)
from aw_server.server import AWFlask


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


def test_server_api_summary_snapshot_serializes_builder_output(monkeypatch):
    app = AWFlask("127.0.0.1", testing=True)
    base = datetime(2026, 3, 1, 10, 0, tzinfo=timezone.utc)
    category_period = f"{base.isoformat()}/{(base + timedelta(hours=1)).isoformat()}"

    def fake_build_summary_snapshot_from_scope(*args, **kwargs):
        return {
            "window": {"duration": "1800"},
            "by_period": {},
            "uncategorized_rows": [{"app": "Antigravity"}],
        }

    monkeypatch.setattr(
        api_module, "build_summary_snapshot_from_scope", fake_build_summary_snapshot_from_scope
    )

    result = app.api.summary_snapshot(
        range_start=base,
        range_end=base + timedelta(hours=1),
        category_periods=[category_period],
        window_buckets=["test-window"],
        afk_buckets=["test-afk"],
        stopwatch_buckets=[],
        filter_afk=True,
        categories=[],
        filter_categories=[],
        always_active_pattern="",
    )

    assert result["window"]["duration"] == 1800.0
    assert result["window"]["app_events"] == []
    assert result["by_period"][category_period] == {"cat_events": []}
    assert result["uncategorized_rows"][0]["title"] == "Antigravity"


def test_server_api_get_checkins_serializes_builder_output(monkeypatch):
    app = AWFlask("127.0.0.1", testing=True)

    def fake_build_checkins_payload(*, date_filter=None):
        assert date_filter == "2026-03-14"
        return {
            "available_dates": ["2026-03-14"],
            "sessions": [{"id": "session-1", "answers": [{"status": "answered"}]}],
        }

    monkeypatch.setattr(api_module, "build_checkins_payload", fake_build_checkins_payload)

    result = app.api.get_checkins(date_filter="2026-03-14")

    assert result["data_source"] == ""
    assert result["available_dates"] == ["2026-03-14"]
    assert result["sessions"][0]["answered_count"] == 1
    assert result["sessions"][0]["skipped_count"] == 0
