from aw_server.summary_snapshot_models import PeriodBound, SummarySegment
from aw_server.summary_snapshot_response import (
    build_snapshot_response,
    empty_summary_snapshot,
    merge_summary_segments,
)


def test_empty_summary_snapshot_backfills_requested_periods():
    periods = [
        "2026-03-01T10:00:00+00:00/2026-03-01T11:00:00+00:00",
        "2026-03-01T11:00:00+00:00/2026-03-01T12:00:00+00:00",
    ]

    result = empty_summary_snapshot(periods)

    assert result["window"]["duration"] == 0
    assert result["window"]["app_events"] == []
    assert list(result["by_period"].keys()) == periods
    assert result["by_period"][periods[0]] == {"cat_events": []}
    assert result["uncategorized_rows"] == []


def test_merge_summary_segments_merges_durations_and_earliest_timestamps():
    base = SummarySegment(
        logical_period="period-1",
        computed_end_ms=2000,
        duration=120,
        apps={"Code": {"duration": 60, "timestamp_ms": 1500}},
        categories={
            '["Code"]': {
                "category": ["Code"],
                "duration": 60,
                "timestamp_ms": 1500,
            }
        },
        uncategorized_apps={"Slack": {"duration": 30, "timestamp_ms": 1800}},
    )
    delta = SummarySegment(
        logical_period="period-1",
        computed_end_ms=4000,
        duration=90,
        apps={
            "Code": {"duration": 15, "timestamp_ms": 900},
            "Docs": {"duration": 45, "timestamp_ms": 2500},
        },
        categories={
            '["Code"]': {
                "category": ["Code"],
                "duration": 15,
                "timestamp_ms": 900,
            },
            '["Docs"]': {
                "category": ["Docs"],
                "duration": 45,
                "timestamp_ms": 2500,
            },
        },
        uncategorized_apps={"Slack": {"duration": 5, "timestamp_ms": 1200}},
    )

    result = merge_summary_segments(base, delta)

    assert result.computed_end_ms == 4000
    assert result.duration == 210
    assert result.apps["Code"] == {"duration": 75.0, "timestamp_ms": 900.0}
    assert result.apps["Docs"] == {"duration": 45.0, "timestamp_ms": 2500.0}
    assert result.categories['["Code"]']["duration"] == 75.0
    assert result.categories['["Code"]']["timestamp_ms"] == 900.0
    assert result.uncategorized_apps["Slack"] == {"duration": 35.0, "timestamp_ms": 1200.0}


def test_build_snapshot_response_aggregates_orders_and_backfills_missing_periods():
    periods = [
        PeriodBound("period-1", 1000, 2000),
        PeriodBound("period-2", 2000, 3000),
    ]
    segments = {
        "period-1": SummarySegment(
            logical_period="period-1",
            computed_end_ms=2000,
            duration=120,
            apps={
                "Code": {"duration": 90, "timestamp_ms": 1100},
                "Docs": {"duration": 30, "timestamp_ms": 1500},
            },
            categories={
                '["Code"]': {
                    "category": ["Code"],
                    "duration": 90,
                    "timestamp_ms": 1100,
                }
            },
            uncategorized_apps={"Slack": {"duration": 25, "timestamp_ms": 1400}},
        ),
        "period-2": SummarySegment(
            logical_period="period-2",
            computed_end_ms=3000,
            duration=60,
            apps={"Code": {"duration": 60, "timestamp_ms": 2100}},
            categories={
                '["Meetings"]': {
                    "category": ["Meetings"],
                    "duration": 60,
                    "timestamp_ms": 2100,
                }
            },
            uncategorized_apps={"Mail": {"duration": 15, "timestamp_ms": 2200}},
        ),
    }

    result = build_snapshot_response(periods, segments)

    assert result["window"]["duration"] == 180.0
    assert [event["data"]["app"] for event in result["window"]["app_events"]] == ["Code", "Docs"]
    assert result["window"]["app_events"][0]["duration"] == 150.0
    assert result["window"]["cat_events"][0]["data"]["$category"] == ["Code"]
    assert result["window"]["cat_events"][1]["data"]["$category"] == ["Meetings"]
    assert result["by_period"]["period-1"]["cat_events"][0]["data"]["$category"] == ["Code"]
    assert result["by_period"]["period-2"]["cat_events"][0]["data"]["$category"] == ["Meetings"]
    assert [row["app"] for row in result["uncategorized_rows"]] == ["Slack", "Mail"]
