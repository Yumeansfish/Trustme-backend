from datetime import datetime, timezone

from aw_server.dashboard_summary_invalidation import build_snapshot_invalidation_targets
from aw_server.dashboard_summary_store import SummarySnapshotStore
from aw_server.dashboard_summary_warmup import build_bucket_records
from aw_server.server import AWFlask


def test_summary_snapshot_store_delete_segments_filters_scope_and_period(tmp_path):
    store = SummarySnapshotStore(testing=True, path=tmp_path / "summary.sqlite")
    payload = {"duration": 1.0, "apps": {}, "categories": {}, "uncategorized_apps": {}}
    store.put_segment(
        "scope-a",
        "period-1",
        computed_end="2026-03-01T00:00:00+00:00",
        stored_at="2026-03-01T00:00:00+00:00",
        payload=payload,
    )
    store.put_segment(
        "scope-a",
        "period-2",
        computed_end="2026-03-02T00:00:00+00:00",
        stored_at="2026-03-02T00:00:00+00:00",
        payload=payload,
    )
    store.put_segment(
        "scope-b",
        "period-1",
        computed_end="2026-03-03T00:00:00+00:00",
        stored_at="2026-03-03T00:00:00+00:00",
        payload=payload,
    )

    deleted = store.delete_segments(scope_key="scope-a", logical_periods=["period-1"])

    assert deleted == 1
    assert store.count_segments() == 2
    assert store.count_segments(scope_key="scope-a") == 1
    assert store.count_segments(scope_key="scope-a", logical_periods=["period-1"]) == 0
    assert store.count_segments(scope_key="scope-b") == 1


def test_set_setting_invalidates_previous_warmup_targets_without_clearing_unrelated_scope():
    app = AWFlask("127.0.0.1", testing=True)
    api = app.api

    created = datetime(2026, 1, 1, 9, 0, tzinfo=timezone.utc)
    api.create_bucket(
        "aw-watcher-window_alpha.local",
        event_type="currentwindow",
        client="test",
        hostname="alpha.local",
        created=created,
    )
    api.create_bucket(
        "aw-watcher-afk_alpha.local",
        event_type="afkstatus",
        client="test",
        hostname="alpha.local",
        created=created,
    )

    previous_settings = {
        "startOfDay": "09:00",
        "startOfWeek": "Monday",
        "deviceMappings": {},
        "classes": [],
    }
    api.settings.data = dict(previous_settings)
    api.settings.save()

    bucket_records = build_bucket_records(api.get_buckets())
    targets = build_snapshot_invalidation_targets(
        settings_data=previous_settings,
        bucket_records=bucket_records,
        now=datetime(2026, 3, 17, 10, 0, tzinfo=timezone.utc),
    )
    assert targets

    payload = {"duration": 1.0, "apps": {}, "categories": {}, "uncategorized_apps": {}}
    for target in targets:
        for logical_period in target["logical_periods"]:
            api.summary_snapshot_store.put_segment(
                target["scope_key"],
                logical_period,
                computed_end="2026-03-17T10:00:00+00:00",
                stored_at="2026-03-17T10:00:00+00:00",
                payload=payload,
            )

    api.summary_snapshot_store.put_segment(
        "manual-unrelated-scope",
        "manual-period",
        computed_end="2026-03-17T10:00:00+00:00",
        stored_at="2026-03-17T10:00:00+00:00",
        payload=payload,
    )

    api.set_setting(
        "classes",
        [{"name": ["Code"], "rule": {"type": "regex", "regex": "Code", "ignore_case": True}}],
    )

    assert api.summary_snapshot_store.count_segments(scope_key="manual-unrelated-scope") == 1
    for target in targets:
        assert (
            api.summary_snapshot_store.count_segments(
                scope_key=target["scope_key"],
                logical_periods=target["logical_periods"],
            )
            == 0
        )
