from datetime import datetime, timezone

from aw_server.dashboard_domain_service import (
    DEFAULT_DEVICE_GROUP_NAME,
    build_ad_hoc_summary_scope,
    build_dashboard_summary_scopes,
    build_settings_backed_summary_scope,
    resolve_default_dashboard_hosts,
    resolve_dashboard_scope,
)


def _bucket(
    bucket_id,
    bucket_type,
    hostname,
    *,
    created,
    last_updated,
):
    return {
        "id": bucket_id,
        "type": bucket_type,
        "hostname": hostname,
        "created": created,
        "first_seen": created,
        "last_updated": last_updated,
        "data": {},
        "metadata": {},
    }


def test_build_dashboard_summary_scopes_applies_grouping_categories_and_stopwatch_semantics():
    settings_data = {
        "startOfDay": "09:00",
        "startOfWeek": "Monday",
        "deviceMappings": {"Research rig": ["rig.local"]},
        "classes": [
            {"name": ["Code"], "rule": {"type": "regex", "regex": "Code", "ignore_case": True}},
            {"name": ["Parent"], "rule": {"type": "none"}},
            {"name": ["Skip"], "rule": {"type": None}},
        ],
        "always_active_pattern": "Zoom|Teams",
    }
    bucket_records = [
        _bucket(
            "aw-watcher-window_alpha.local",
            "currentwindow",
            "alpha.local",
            created="2026-01-01T09:00:00+01:00",
            last_updated="2026-03-13T10:00:00+01:00",
        ),
        _bucket(
            "aw-watcher-afk_alpha.local",
            "afkstatus",
            "alpha.local",
            created="2026-01-01T09:00:00+01:00",
            last_updated="2026-03-13T10:00:00+01:00",
        ),
        _bucket(
            "aw-watcher-window_rig.local",
            "currentwindow",
            "rig.local",
            created="2026-01-01T09:00:00+01:00",
            last_updated="2026-03-13T10:00:00+01:00",
        ),
        _bucket(
            "aw-watcher-afk_rig.local",
            "afkstatus",
            "rig.local",
            created="2026-01-01T09:00:00+01:00",
            last_updated="2026-03-13T10:00:00+01:00",
        ),
        _bucket(
            "aw-stopwatch",
            "general.stopwatch",
            "unknown",
            created="2026-01-01T09:00:00+01:00",
            last_updated="2026-03-13T10:00:00+01:00",
        ),
        _bucket(
            "aw-watcher-web-firefox",
            "web.tab.current",
            "unknown",
            created="2026-01-01T09:00:00+01:00",
            last_updated="2026-03-13T10:00:00+01:00",
        ),
    ]

    scopes = build_dashboard_summary_scopes(
        settings_data=settings_data,
        bucket_records=bucket_records,
    )

    default_scope = next(scope for scope in scopes if scope.group_name == DEFAULT_DEVICE_GROUP_NAME)
    rig_scope = next(scope for scope in scopes if scope.group_name == "Research rig")

    assert default_scope.hosts == ["alpha.local"]
    assert default_scope.window_buckets == ["aw-watcher-window_alpha.local"]
    assert default_scope.afk_buckets == ["aw-watcher-afk_alpha.local"]
    assert default_scope.stopwatch_buckets == ["aw-stopwatch"]
    assert default_scope.categories == [
        [["Code"], {"type": "regex", "regex": "Code", "ignore_case": True}],
        [["Parent"], {"type": "none"}],
    ]
    assert default_scope.filter_afk is True
    assert default_scope.always_active_pattern == "Zoom|Teams"

    assert rig_scope.hosts == ["rig.local"]
    assert rig_scope.window_buckets == ["aw-watcher-window_rig.local"]
    assert rig_scope.afk_buckets == ["aw-watcher-afk_rig.local"]
    assert rig_scope.stopwatch_buckets == ["aw-stopwatch"]


def test_build_ad_hoc_summary_scope_deduplicates_request_payload():
    scope = build_ad_hoc_summary_scope(
        window_buckets=["window-a", "window-a", "window-b"],
        afk_buckets=["afk-a", "afk-a"],
        stopwatch_buckets=["stopwatch-a", "stopwatch-a"],
        filter_afk=True,
        categories=[
            {"name": ["Code"], "rule": {"type": "regex", "regex": "Code", "ignore_case": True}},
            {"name": ["Skip"], "rule": {"type": None}},
        ],
        filter_categories=[["Code"], ["Code"], ["Design"]],
        always_active_pattern="Zoom",
    )

    assert scope.window_buckets == ["window-a", "window-b"]
    assert scope.afk_buckets == ["afk-a"]
    assert scope.stopwatch_buckets == ["stopwatch-a"]
    assert scope.categories == [[["Code"], {"type": "regex", "regex": "Code", "ignore_case": True}]]
    assert scope.filter_categories == [["Code"], ["Design"]]
    assert scope.always_active_pattern == "Zoom"


def test_build_settings_backed_summary_scope_uses_normalized_backend_settings():
    scope = build_settings_backed_summary_scope(
        settings_data={
            "classes": [
                {"name": ["Code"], "rule": {"type": "regex", "regex": "Code", "ignore_case": True}},
                {"name": ["Skip"], "rule": {"type": None}},
            ],
            "alwaysActivePattern": "Teams",
        },
        window_buckets=["window-a", "window-a"],
        afk_buckets=["afk-a"],
        stopwatch_buckets=["stopwatch-a", "stopwatch-a"],
        filter_afk=True,
        filter_categories=[["Code"], ["Code"], ["Design"]],
    )

    assert scope.window_buckets == ["window-a"]
    assert scope.afk_buckets == ["afk-a"]
    assert scope.stopwatch_buckets == ["stopwatch-a"]
    assert scope.categories == [[["Code"], {"type": "regex", "regex": "Code", "ignore_case": True}]]
    assert scope.filter_categories == [["Code"], ["Design"]]
    assert scope.always_active_pattern == "Teams"


def test_resolve_dashboard_scope_expands_groups_and_applies_overlap_filtering():
    settings_data = {
        "startOfDay": "09:00",
        "startOfWeek": "Monday",
        "deviceMappings": {"Research rig": ["rig.local", "lab.local"]},
        "classes": [],
        "always_active_pattern": "",
    }
    bucket_records = [
        _bucket(
            "aw-watcher-window_rig.local",
            "currentwindow",
            "rig.local",
            created="2026-01-01T09:00:00+01:00",
            last_updated="2026-03-13T10:00:00+01:00",
        ),
        _bucket(
            "aw-watcher-afk_rig.local",
            "afkstatus",
            "rig.local",
            created="2026-01-01T09:00:00+01:00",
            last_updated="2026-03-13T10:00:00+01:00",
        ),
        _bucket(
            "aw-watcher-window_lab.local",
            "currentwindow",
            "lab.local",
            created="2026-01-01T09:00:00+01:00",
            last_updated="2026-02-01T09:00:00+01:00",
        ),
        _bucket(
            "aw-watcher-afk_lab.local",
            "afkstatus",
            "lab.local",
            created="2026-01-01T09:00:00+01:00",
            last_updated="2026-02-01T09:00:00+01:00",
        ),
        _bucket(
            "aw-stopwatch",
            "general.stopwatch",
            "unknown",
            created="2026-01-01T09:00:00+01:00",
            last_updated="2026-03-13T10:00:00+01:00",
        ),
        _bucket(
            "aw-watcher-web-firefox",
            "web.tab.current",
            "unknown",
            created="2026-01-01T09:00:00+01:00",
            last_updated="2026-03-13T10:00:00+01:00",
        ),
    ]

    overlap_start_ms = datetime(2026, 3, 10, 0, 0, tzinfo=timezone.utc).timestamp() * 1000
    overlap_end_ms = datetime(2026, 3, 14, 0, 0, tzinfo=timezone.utc).timestamp() * 1000

    result = resolve_dashboard_scope(
        settings_data=settings_data,
        bucket_records=bucket_records,
        requested_hosts=["rig.local"],
        overlap_start_ms=overlap_start_ms,
        overlap_end_ms=overlap_end_ms,
    )

    assert result.requested_hosts == ["rig.local"]
    assert result.resolved_hosts == ["rig.local"]
    assert result.window_buckets == ["aw-watcher-window_rig.local"]
    assert result.afk_buckets == ["aw-watcher-afk_rig.local"]
    assert result.browser_buckets == ["aw-watcher-web-firefox"]
    assert result.stopwatch_buckets == ["aw-stopwatch"]


def test_resolve_default_dashboard_hosts_prefers_backend_device_groups():
    settings_data = {
        "deviceMappings": {"Research rig": ["rig.local", "lab.local"]},
        "classes": [],
        "always_active_pattern": "",
    }
    bucket_records = [
        _bucket(
            "aw-watcher-window_rig.local",
            "currentwindow",
            "rig.local",
            created="2026-01-01T09:00:00+01:00",
            last_updated="2026-03-13T10:00:00+01:00",
        ),
        _bucket(
            "aw-watcher-afk_rig.local",
            "afkstatus",
            "rig.local",
            created="2026-01-01T09:00:00+01:00",
            last_updated="2026-03-13T10:00:00+01:00",
        ),
        _bucket(
            "aw-watcher-window_lab.local",
            "currentwindow",
            "lab.local",
            created="2026-01-01T09:00:00+01:00",
            last_updated="2026-02-01T09:00:00+01:00",
        ),
        _bucket(
            "aw-watcher-afk_lab.local",
            "afkstatus",
            "lab.local",
            created="2026-01-01T09:00:00+01:00",
            last_updated="2026-02-01T09:00:00+01:00",
        ),
    ]

    assert resolve_default_dashboard_hosts(
        settings_data=settings_data,
        bucket_records=bucket_records,
    ) == ["rig.local", "lab.local"]
