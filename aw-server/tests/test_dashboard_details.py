from datetime import datetime, timedelta, timezone

from aw_core.models import Event

from aw_server.dashboard_details import build_dashboard_details


class FakeBucket:
    def __init__(self, events):
        self.events = list(events)

    def get(self, limit=-1, start=None, end=None):
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


def test_build_dashboard_details_aggregates_browser_focus_and_stopwatch_data():
    base = datetime(2026, 3, 1, 10, 0, tzinfo=timezone.utc)
    db = FakeDB(
        {
            "window-a": FakeBucket(
                [
                    Event(
                        timestamp=base,
                        duration=1800,
                        data={"app": "Firefox", "title": "Gmail"},
                    ),
                    Event(
                        timestamp=base + timedelta(minutes=30),
                        duration=1800,
                        data={"app": "Code", "title": "main.py"},
                    ),
                ]
            ),
            "aw-watcher-web-firefox": FakeBucket(
                [
                    Event(
                        timestamp=base,
                        duration=900,
                        data={"url": "https://example.com/a", "title": "Example A"},
                    ),
                    Event(
                        timestamp=base + timedelta(minutes=10),
                        duration=900,
                        data={"url": "https://example.com/b", "title": "Example B"},
                    ),
                    Event(
                        timestamp=base + timedelta(minutes=40),
                        duration=600,
                        data={"url": "https://ignored.dev", "title": "Ignored"},
                    ),
                ]
            ),
            "stopwatch-a": FakeBucket(
                [
                    Event(
                        timestamp=base + timedelta(minutes=50),
                        duration=300,
                        data={"label": "Break", "running": False},
                    ),
                    Event(
                        timestamp=base + timedelta(minutes=55),
                        duration=120,
                        data={"label": "Break", "running": False},
                    ),
                ]
            ),
        }
    )

    result = build_dashboard_details(
        db,
        range_start=base,
        range_end=base + timedelta(hours=1),
        window_buckets=["window-a"],
        browser_buckets=["aw-watcher-web-firefox"],
        stopwatch_buckets=["stopwatch-a"],
    )

    assert result["browser"]["duration"] == 1800
    assert result["browser"]["domains"][0]["data"]["$domain"] == "example.com"
    assert result["browser"]["domains"][0]["duration"] == 1800
    assert result["browser"]["titles"][0]["data"]["title"] == "Example A"
    assert result["stopwatch"]["stopwatch_events"][0]["data"]["label"] == "Break"
    assert result["stopwatch"]["stopwatch_events"][0]["duration"] == 420
