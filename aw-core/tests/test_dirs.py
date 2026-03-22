import importlib.util
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "aw_core" / "dirs.py"
SPEC = importlib.util.spec_from_file_location("aw_core_dirs", MODULE_PATH)
assert SPEC and SPEC.loader
dirs = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(dirs)


def test_prefer_runtime_root_uses_trust_me_for_fresh_installs(tmp_path):
    trust_me = tmp_path / "trust-me"
    legacy = tmp_path / "activitywatch"

    assert dirs._prefer_runtime_root(str(trust_me), str(legacy)) == str(trust_me)


def test_prefer_runtime_root_falls_back_to_legacy_when_needed(tmp_path):
    trust_me = tmp_path / "trust-me"
    legacy = tmp_path / "activitywatch"
    legacy.mkdir()

    assert dirs._prefer_runtime_root(str(trust_me), str(legacy)) == str(legacy)


def test_prefer_runtime_root_keeps_trust_me_when_both_exist(tmp_path):
    trust_me = tmp_path / "trust-me"
    legacy = tmp_path / "activitywatch"
    trust_me.mkdir()
    legacy.mkdir()

    assert dirs._prefer_runtime_root(str(trust_me), str(legacy)) == str(trust_me)


def test_get_config_dir_uses_legacy_root_when_present(tmp_path, monkeypatch):
    legacy = tmp_path / "activitywatch"
    legacy.mkdir()

    monkeypatch.setattr(dirs.platformdirs, "user_config_dir", lambda app: str(tmp_path / app))

    path = Path(dirs.get_config_dir("aw-core-test"))

    assert path == legacy / "aw-core-test"
    assert path.exists()


def test_get_log_dir_uses_trust_me_root_for_fresh_installs(tmp_path, monkeypatch):
    monkeypatch.setattr(dirs.sys, "platform", "linux")
    monkeypatch.setattr(
        dirs.platformdirs,
        "user_cache_path",
        lambda app: tmp_path / app,
    )

    path = Path(dirs.get_log_dir("aw-core-test"))

    assert path == tmp_path / "trust-me" / "log" / "aw-core-test"
    assert path.exists()
