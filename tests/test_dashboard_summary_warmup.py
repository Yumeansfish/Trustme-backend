from datetime import datetime
from zoneinfo import ZoneInfo

from aw_server.dashboard_summary_warmup import build_dashboard_summary_warmup_jobs


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


def test_build_dashboard_summary_warmup_jobs_uses_period_specific_ranges():
    tz = ZoneInfo("Europe/Zurich")
    now = datetime(2026, 3, 13, 12, 0, tzinfo=tz)
    settings_data = {
        "startOfDay": "04:00",
        "startOfWeek": "Monday",
        "deviceMappings": {},
        "classes": [
            {"name": ["Code"], "rule": {"type": "regex", "regex": "Code", "ignore_case": True}},
            {"name": ["Parent"], "rule": {"type": "none"}},
            {"name": ["Skip"], "rule": {"type": None}},
        ],
    }
    bucket_records = [
        _bucket(
            "aw-watcher-window_alpha.local",
            "currentwindow",
            "alpha.local",
            created="2026-01-01T04:00:00+01:00",
            last_updated="2026-03-13T11:59:59+01:00",
        ),
        _bucket(
            "aw-watcher-afk_alpha.local",
            "afkstatus",
            "alpha.local",
            created="2026-01-01T04:00:00+01:00",
            last_updated="2026-03-13T11:59:59+01:00",
        ),
        _bucket(
            "aw-watcher-window_beta.local",
            "currentwindow",
            "beta.local",
            created="2026-02-01T04:00:00+01:00",
            last_updated="2026-03-13T11:59:59+01:00",
        ),
        _bucket(
            "aw-watcher-afk_beta.local",
            "afkstatus",
            "beta.local",
            created="2026-02-01T04:00:00+01:00",
            last_updated="2026-03-13T11:59:59+01:00",
        ),
        _bucket(
            "aw-stopwatch",
            "general.stopwatch",
            "unknown",
            created="2026-03-01T04:00:00+01:00",
            last_updated="2026-03-13T11:59:59+01:00",
        ),
    ]

    jobs = build_dashboard_summary_warmup_jobs(
        settings_data=settings_data,
        bucket_records=bucket_records,
        now=now,
        local_timezone=tz,
    )

    assert [job.period_name for job in jobs] == ["year", "month", "week"]

    year_job = jobs[0]
    month_job = jobs[1]
    week_job = jobs[2]

    assert year_job.group_name == "My macbook"
    assert year_job.logical_periods[0] == "2026-01-01T04:00:00+01:00/2026-02-01T04:00:00+01:00"
    assert month_job.logical_periods[0] == "2026-03-01T04:00:00+01:00/2026-03-02T04:00:00+01:00"
    assert week_job.logical_periods[0] == "2026-03-09T04:00:00+01:00/2026-03-10T04:00:00+01:00"

    assert year_job.window_buckets == [
        "aw-watcher-window_alpha.local",
        "aw-watcher-window_beta.local",
    ]
    assert year_job.afk_buckets == [
        "aw-watcher-afk_alpha.local",
        "aw-watcher-afk_beta.local",
    ]
    assert year_job.stopwatch_buckets == ["aw-stopwatch"]
    assert year_job.categories == [
        [["Code"], {"type": "regex", "regex": "Code", "ignore_case": True}],
        [["Parent"], {"type": "none"}],
    ]


def test_build_dashboard_summary_warmup_jobs_filters_out_non_overlapping_hosts_and_keeps_custom_groups():
    tz = ZoneInfo("Europe/Zurich")
    now = datetime(2026, 3, 13, 12, 0, tzinfo=tz)
    settings_data = {
        "startOfDay": "04:00",
        "startOfWeek": "Monday",
        "deviceMappings": {
            "Research rig": ["rig.local"],
            "My macbook": ["ignored-by-default-group.local"],
        },
        "classes": [],
    }
    bucket_records = [
        _bucket(
            "aw-watcher-window_alpha.local",
            "currentwindow",
            "alpha.local",
            created="2026-01-01T04:00:00+01:00",
            last_updated="2026-03-13T11:59:59+01:00",
        ),
        _bucket(
            "aw-watcher-afk_alpha.local",
            "afkstatus",
            "alpha.local",
            created="2026-01-01T04:00:00+01:00",
            last_updated="2026-03-13T11:59:59+01:00",
        ),
        _bucket(
            "aw-watcher-window_old.local",
            "currentwindow",
            "old.local",
            created="2025-01-01T04:00:00+01:00",
            last_updated="2025-01-15T04:00:00+01:00",
        ),
        _bucket(
            "aw-watcher-afk_old.local",
            "afkstatus",
            "old.local",
            created="2025-01-01T04:00:00+01:00",
            last_updated="2025-01-15T04:00:00+01:00",
        ),
        _bucket(
            "aw-watcher-window_rig.local",
            "currentwindow",
            "rig.local",
            created="2026-02-01T04:00:00+01:00",
            last_updated="2026-03-13T11:59:59+01:00",
        ),
        _bucket(
            "aw-watcher-afk_rig.local",
            "afkstatus",
            "rig.local",
            created="2026-02-01T04:00:00+01:00",
            last_updated="2026-03-13T11:59:59+01:00",
        ),
    ]

    jobs = build_dashboard_summary_warmup_jobs(
        settings_data=settings_data,
        bucket_records=bucket_records,
        now=now,
        local_timezone=tz,
    )

    month_jobs = [job for job in jobs if job.period_name == "month"]
    default_month_job = next(job for job in month_jobs if job.group_name == "My macbook")
    rig_month_job = next(job for job in month_jobs if job.group_name == "Research rig")

    assert default_month_job.window_buckets == ["aw-watcher-window_alpha.local"]
    assert default_month_job.afk_buckets == ["aw-watcher-afk_alpha.local"]
    assert rig_month_job.window_buckets == ["aw-watcher-window_rig.local"]
    assert rig_month_job.afk_buckets == ["aw-watcher-afk_rig.local"]
