import random
from datetime import datetime, timedelta, timezone

import pytest
from aw_core.models import Event
from aw_server.dashboard_summary_store import SummarySnapshotStore
from aw_server.summary_snapshot import build_summary_snapshot
from aw_server.server import AWFlask


@pytest.fixture()
def bucket(flask_client):
    "Context manager for creating and deleting a testing bucket"
    try:
        bucket_id = "test"
        r = flask_client.post(
            f"/api/0/buckets/{bucket_id}",
            json={"client": "test", "type": "test", "hostname": "test"},
        )
        assert r.status_code == 200
        yield bucket_id
    finally:
        r = flask_client.delete(f"/api/0/buckets/{bucket_id}")
        assert r.status_code == 200


def test_info(flask_client):
    r = flask_client.get("/api/0/info")
    assert r.status_code == 200
    assert r.json["testing"]


def test_buckets(flask_client, bucket, benchmark):
    @benchmark
    def list_buckets():
        r = flask_client.get("/api/0/buckets/")
        print(r.json)
        assert r.status_code == 200
        assert len(r.json) == 1


def test_heartbeats(flask_client, bucket, benchmark):
    # FIXME: Currently tests using the memory storage method
    # TODO: Test with a longer data section and see if there's a significant difference
    # TODO: Test with a larger bucket and see if there's a significant difference
    @benchmark
    def heartbeat():
        now = datetime.now()
        r = flask_client.post(
            f"/api/0/buckets/{bucket}/heartbeat?pulsetime=1",
            json={"timestamp": now, "duration": 0, "data": {"random": random.random()}},
        )
        assert r.status_code == 200


def test_get_events(flask_client, bucket, benchmark):
    n_events = 100
    start_time = datetime.now() - timedelta(days=100)
    for i in range(n_events):
        now = start_time + timedelta(hours=i)
        r = flask_client.post(
            f"/api/0/buckets/{bucket}/heartbeat?pulsetime=0",
            json={"timestamp": now, "duration": 0, "data": {"random": random.random()}},
        )
        assert r.status_code == 200

    @benchmark
    def get_events():
        r = flask_client.get(f"/api/0/buckets/{bucket}/events")
        assert r.status_code == 200
        assert r.json
        assert len(r.json) == n_events

        r = flask_client.get(f"/api/0/buckets/{bucket}/events?limit=-1")
        assert r.status_code == 200
        assert r.json
        assert len(r.json) == n_events

        r = flask_client.get(f"/api/0/buckets/{bucket}/events?limit=10")
        assert r.status_code == 200
        assert r.json
        assert len(r.json) == 10

        r = flask_client.get(f"/api/0/buckets/{bucket}/events?limit=100")
        assert r.status_code == 200
        assert r.json
        assert len(r.json) == n_events

        r = flask_client.get(f"/api/0/buckets/{bucket}/events?limit=1000")
        assert r.status_code == 200
        assert r.json
        assert len(r.json) == n_events


class FakeBucket:
    def __init__(self, events):
        self.events = list(events)
        self.calls = []

    def get(self, limit=-1, start=None, end=None):
        self.calls.append((limit, start, end))
        filtered = [
            event
            for event in self.events
            if (start is None or event.timestamp < end)
            and (end is None or event.timestamp + event.duration > start)
        ]
        if limit == -1:
            return filtered
        return filtered[:limit]


class FakeDB:
    def __init__(self, buckets):
        self._buckets = buckets

    def buckets(self):
        return {bucket_id: {} for bucket_id in self._buckets}

    def __getitem__(self, bucket_id):
        return self._buckets[bucket_id]


def test_summary_snapshot():
    base = datetime(2026, 3, 1, 10, 0, tzinfo=timezone.utc)
    db = FakeDB(
        {
            "test-window": FakeBucket(
                [
                    Event(
                        timestamp=base,
                        duration=1800,
                        data={"app": "Firefox", "title": "Gmail"},
                    ),
                    Event(
                        timestamp=base + timedelta(minutes=30),
                        duration=1800,
                        data={"app": "Code", "title": "aw-webui"},
                    ),
                ]
            ),
            "test-afk": FakeBucket(
                [
                    Event(
                        timestamp=base - timedelta(minutes=5),
                        duration=4200,
                        data={"status": "not-afk"},
                    )
                ]
            ),
        }
    )

    category_periods = [
        f"{base.isoformat()}/{(base + timedelta(minutes=30)).isoformat()}",
        f"{(base + timedelta(minutes=30)).isoformat()}/{(base + timedelta(hours=1)).isoformat()}",
    ]
    result = build_summary_snapshot(
        db,
        range_start=base,
        range_end=base + timedelta(hours=1),
        category_periods=category_periods,
        window_buckets=["test-window"],
        afk_buckets=["test-afk"],
        stopwatch_buckets=[],
        filter_afk=True,
        categories=[
            [["Email"], {"type": "regex", "regex": "Firefox|Gmail", "ignore_case": True}],
            [["Code"], {"type": "regex", "regex": "Code", "ignore_case": True}],
        ],
        filter_categories=[],
        always_active_pattern="",
    )

    window = result["window"]
    assert window["duration"] == pytest.approx(3600)
    assert [event["data"]["app"] for event in window["app_events"]] == ["Firefox", "Code"]
    assert [event["data"]["$category"] for event in window["cat_events"]] == [["Email"], ["Code"]]
    assert result["uncategorized_rows"] == []

    by_period = result["by_period"]
    first_period, second_period = category_periods
    assert by_period[first_period]["cat_events"][0]["data"]["$category"] == ["Email"]
    assert by_period[first_period]["cat_events"][0]["duration"] == pytest.approx(1800)
    assert by_period[second_period]["cat_events"][0]["data"]["$category"] == ["Code"]
    assert by_period[second_period]["cat_events"][0]["duration"] == pytest.approx(1800)


def test_summary_snapshot_expands_range_to_cover_category_periods():
    base = datetime(2026, 3, 1, 10, 0, tzinfo=timezone.utc)
    db = FakeDB(
        {
            "test-window": FakeBucket(
                [
                    Event(
                        timestamp=base,
                        duration=1800,
                        data={"app": "Firefox", "title": "Gmail"},
                    ),
                    Event(
                        timestamp=base + timedelta(minutes=30),
                        duration=1800,
                        data={"app": "Code", "title": "aw-webui"},
                    ),
                ]
            ),
            "test-afk": FakeBucket(
                [
                    Event(
                        timestamp=base - timedelta(minutes=5),
                        duration=4200,
                        data={"status": "not-afk"},
                    )
                ]
            ),
        }
    )

    category_periods = [
        f"{base.isoformat()}/{(base + timedelta(minutes=30)).isoformat()}",
        f"{(base + timedelta(minutes=30)).isoformat()}/{(base + timedelta(hours=1)).isoformat()}",
    ]
    result = build_summary_snapshot(
        db,
        range_start=base,
        range_end=base + timedelta(minutes=30),
        category_periods=category_periods,
        window_buckets=["test-window"],
        afk_buckets=["test-afk"],
        stopwatch_buckets=[],
        filter_afk=True,
        categories=[
            [["Email"], {"type": "regex", "regex": "Firefox|Gmail", "ignore_case": True}],
            [["Code"], {"type": "regex", "regex": "Code", "ignore_case": True}],
        ],
        filter_categories=[],
        always_active_pattern="",
    )

    window = result["window"]
    first_period, second_period = category_periods
    assert window["duration"] == pytest.approx(3600)
    assert result["by_period"][first_period]["cat_events"][0]["duration"] == pytest.approx(1800)
    assert result["by_period"][second_period]["cat_events"][0]["duration"] == pytest.approx(1800)
    assert result["uncategorized_rows"] == []


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
        "categories": [],
        "filter_categories": [],
        "always_active_pattern": "",
    }

    r = flask_client.post("/api/0/dashboard/summary-snapshot", json=payload)
    assert r.status_code == 200
    assert r.json == expected
    assert captured["range_start"] == base
    assert captured["range_end"] == base + timedelta(hours=1)
    assert captured["category_periods"] == category_periods
    assert captured["window_buckets"] == ["test-window"]


def test_summary_snapshot_reuses_persisted_closed_period(tmp_path):
    base = datetime(2026, 3, 1, 10, 0, tzinfo=timezone.utc)
    window_bucket = FakeBucket(
        [
            Event(
                timestamp=base,
                duration=1800,
                data={"app": "Firefox", "title": "Gmail"},
            )
        ]
    )
    afk_bucket = FakeBucket(
        [
            Event(
                timestamp=base - timedelta(minutes=5),
                duration=2400,
                data={"status": "not-afk"},
            )
        ]
    )
    db = FakeDB({"test-window": window_bucket, "test-afk": afk_bucket})
    store = SummarySnapshotStore(testing=True, path=tmp_path / "summary-cache.sqlite")
    logical_period = f"{base.isoformat()}/{(base + timedelta(hours=1)).isoformat()}"

    first = build_summary_snapshot(
        db,
        range_start=base,
        range_end=base + timedelta(hours=1),
        category_periods=[logical_period],
        window_buckets=["test-window"],
        afk_buckets=["test-afk"],
        stopwatch_buckets=[],
        filter_afk=True,
        categories=[
            [["Email"], {"type": "regex", "regex": "Firefox|Gmail", "ignore_case": True}],
        ],
        filter_categories=[],
        always_active_pattern="",
        store=store,
    )
    first_window_calls = len(window_bucket.calls)
    first_afk_calls = len(afk_bucket.calls)

    second = build_summary_snapshot(
        db,
        range_start=base,
        range_end=base + timedelta(hours=1),
        category_periods=[logical_period],
        window_buckets=["test-window"],
        afk_buckets=["test-afk"],
        stopwatch_buckets=[],
        filter_afk=True,
        categories=[
            [["Email"], {"type": "regex", "regex": "Firefox|Gmail", "ignore_case": True}],
        ],
        filter_categories=[],
        always_active_pattern="",
        store=store,
    )

    assert second == first
    assert len(window_bucket.calls) == first_window_calls
    assert len(afk_bucket.calls) == first_afk_calls


def test_summary_snapshot_updates_open_period_incrementally(tmp_path):
    base = datetime(2026, 3, 1, 10, 0, tzinfo=timezone.utc)
    window_bucket = FakeBucket(
        [
            Event(
                timestamp=base,
                duration=1800,
                data={"app": "Firefox", "title": "Gmail"},
            ),
            Event(
                timestamp=base + timedelta(minutes=30),
                duration=1800,
                data={"app": "Code", "title": "aw-webui"},
            ),
        ]
    )
    afk_bucket = FakeBucket(
        [
            Event(
                timestamp=base - timedelta(minutes=5),
                duration=4200,
                data={"status": "not-afk"},
            )
        ]
    )
    db = FakeDB({"test-window": window_bucket, "test-afk": afk_bucket})
    store = SummarySnapshotStore(testing=True, path=tmp_path / "summary-cache.sqlite")
    logical_period = f"{base.isoformat()}/{(base + timedelta(hours=2)).isoformat()}"

    first = build_summary_snapshot(
        db,
        range_start=base,
        range_end=base + timedelta(minutes=30),
        category_periods=[logical_period],
        window_buckets=["test-window"],
        afk_buckets=["test-afk"],
        stopwatch_buckets=[],
        filter_afk=True,
        categories=[],
        filter_categories=[],
        always_active_pattern="",
        store=store,
        now=base + timedelta(minutes=30),
    )
    assert first["window"]["duration"] == pytest.approx(1800)

    second = build_summary_snapshot(
        db,
        range_start=base,
        range_end=base + timedelta(hours=1),
        category_periods=[logical_period],
        window_buckets=["test-window"],
        afk_buckets=["test-afk"],
        stopwatch_buckets=[],
        filter_afk=True,
        categories=[],
        filter_categories=[],
        always_active_pattern="",
        store=store,
        now=base + timedelta(hours=1),
    )
    assert second["window"]["duration"] == pytest.approx(3600)
    assert any(
        start is not None and start >= base + timedelta(minutes=30)
        for _, start, _ in window_bucket.calls[1:]
    )


def test_summary_snapshot_returns_uncategorized_rows_independent_of_category_filters():
    base = datetime(2026, 3, 1, 10, 0, tzinfo=timezone.utc)
    db = FakeDB(
        {
            "test-window": FakeBucket(
                [
                    Event(
                        timestamp=base,
                        duration=1800,
                        data={"app": "Antigravity", "title": "Prototype"},
                    ),
                    Event(
                        timestamp=base + timedelta(minutes=30),
                        duration=1800,
                        data={"app": "Code", "title": "trust-me"},
                    ),
                ]
            ),
            "test-afk": FakeBucket(
                [
                    Event(
                        timestamp=base - timedelta(minutes=5),
                        duration=4200,
                        data={"status": "not-afk"},
                    )
                ]
            ),
        }
    )

    category_periods = [
        f"{base.isoformat()}/{(base + timedelta(hours=1)).isoformat()}",
    ]
    result = build_summary_snapshot(
        db,
        range_start=base,
        range_end=base + timedelta(hours=1),
        category_periods=category_periods,
        window_buckets=["test-window"],
        afk_buckets=["test-afk"],
        stopwatch_buckets=[],
        filter_afk=True,
        categories=[
            [["Code"], {"type": "regex", "regex": "Code", "ignore_case": True}],
        ],
        filter_categories=[["Code"]],
        always_active_pattern="",
    )

    assert [event["data"]["app"] for event in result["window"]["app_events"]] == ["Code"]
    assert result["uncategorized_rows"] == [
        {
            "key": "Antigravity",
            "app": "Antigravity",
            "title": "Antigravity",
            "subtitle": "",
            "duration": pytest.approx(1800),
            "matchText": "Antigravity",
        }
    ]


# TODO: Add benchmark for basic AFK-filtering query
