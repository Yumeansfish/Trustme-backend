import json
from datetime import datetime, timezone

import pytest
from aw_server.dashboard_summary_invalidation import build_snapshot_invalidation_targets
from aw_server.dashboard_summary_warmup import build_bucket_records
from aw_server.exceptions import BadRequest
from aw_server.server import AWFlask
from aw_server.settings import Settings
from aw_server.settings_schema import (
    CURRENT_CATEGORIZATION_KNOWLEDGEBASE_VERSION,
    SETTINGS_SCHEMA_VERSION,
)


def test_settings_loads_backend_owned_defaults(tmp_path):
    settings = Settings(testing=True, path=tmp_path / "settings.json")
    payload = settings.get("")

    assert payload["startOfDay"] == "09:00"
    assert payload["startOfWeek"] == "Monday"
    assert payload["always_active_pattern"] == ""
    assert payload["deviceMappings"] == {}
    assert payload["categorizationKnowledgebaseVersion"] == CURRENT_CATEGORIZATION_KNOWLEDGEBASE_VERSION
    assert payload["_schema_version"] == SETTINGS_SCHEMA_VERSION
    assert isinstance(payload["classes"], list)
    assert payload["classes"]
    assert any(category["name"] == ["Code"] for category in payload["classes"])


def test_server_api_returns_backend_defaults_for_dashboard_settings():
    app = AWFlask("127.0.0.1", testing=True)

    assert app.api.get_setting("startOfDay") == "09:00"
    assert app.api.get_setting("startOfWeek") == "Monday"
    assert app.api.get_setting("always_active_pattern") == ""
    assert app.api.get_setting("deviceMappings") == {}
    assert app.api.get_setting("classes")


def test_settings_migrates_aliases_and_invalid_legacy_values(tmp_path):
    path = tmp_path / "settings.json"
    path.write_text(
        json.dumps(
            {
                "alwaysActivePattern": "Zoom",
                "startOfDay": "9:00",
                "startOfWeek": "Tuesday",
                "deviceMappings": {" My Group ": [" alpha.local ", "alpha.local", ""]},
            }
        )
    )

    settings = Settings(testing=True, path=path)
    payload = settings.get("")

    assert "alwaysActivePattern" not in payload
    assert payload["always_active_pattern"] == "Zoom"
    assert payload["startOfDay"] == "09:00"
    assert payload["startOfWeek"] == "Monday"
    assert payload["deviceMappings"] == {"My Group": ["alpha.local"]}
    assert payload["_schema_version"] == SETTINGS_SCHEMA_VERSION


def test_validated_setting_updates_do_not_invalidate_on_normalized_noop():
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

    previous_settings = api.settings.get("")
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

    before = api.summary_snapshot_store.count_segments()
    assert api.set_setting("startOfDay", "9:00") == "09:00"
    after = api.summary_snapshot_store.count_segments()

    assert before == after


def test_invalid_dashboard_setting_update_is_rejected():
    app = AWFlask("127.0.0.1", testing=True)

    with pytest.raises(BadRequest):
        app.api.set_setting("startOfWeek", "Tuesday")
