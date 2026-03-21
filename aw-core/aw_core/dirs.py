import os
import sys
from functools import wraps
from typing import Callable, Optional

import platformdirs

GetDirFunc = Callable[[Optional[str]], str]
TRUST_ME_APP_NAME = "trust-me"
LEGACY_APP_NAME = "activitywatch"


def ensure_path_exists(path: str) -> None:
    if not os.path.exists(path):
        os.makedirs(path)


def _ensure_returned_path_exists(f: GetDirFunc) -> GetDirFunc:
    @wraps(f)
    def wrapper(subpath: Optional[str] = None) -> str:
        path = f(subpath)
        ensure_path_exists(path)
        return path

    return wrapper


def _prefer_runtime_root(primary_root: str, legacy_root: str) -> str:
    """Use Trust-me roots for fresh installs, but keep existing legacy roots working."""
    if os.path.exists(primary_root):
        return primary_root
    if os.path.exists(legacy_root):
        return legacy_root
    return primary_root


def _resolve_runtime_path(
    primary_root: str, legacy_root: str, module_name: Optional[str] = None
) -> str:
    root = _prefer_runtime_root(primary_root, legacy_root)
    return os.path.join(root, module_name) if module_name else root


@_ensure_returned_path_exists
def get_data_dir(module_name: Optional[str] = None) -> str:
    return _resolve_runtime_path(
        platformdirs.user_data_dir(TRUST_ME_APP_NAME),
        platformdirs.user_data_dir(LEGACY_APP_NAME),
        module_name,
    )


@_ensure_returned_path_exists
def get_cache_dir(module_name: Optional[str] = None) -> str:
    return _resolve_runtime_path(
        platformdirs.user_cache_dir(TRUST_ME_APP_NAME),
        platformdirs.user_cache_dir(LEGACY_APP_NAME),
        module_name,
    )


@_ensure_returned_path_exists
def get_config_dir(module_name: Optional[str] = None) -> str:
    return _resolve_runtime_path(
        platformdirs.user_config_dir(TRUST_ME_APP_NAME),
        platformdirs.user_config_dir(LEGACY_APP_NAME),
        module_name,
    )


@_ensure_returned_path_exists
def get_log_dir(module_name: Optional[str] = None) -> str:  # pragma: no cover
    # on Linux/Unix, platformdirs changed to using XDG_STATE_HOME instead of XDG_DATA_HOME for log_dir in v2.6
    # we want to keep using XDG_DATA_HOME for backwards compatibility
    # https://github.com/ActivityWatch/aw-core/pull/122#issuecomment-1768020335
    if sys.platform.startswith("linux"):
        log_dir = _resolve_runtime_path(
            str(platformdirs.user_cache_path(TRUST_ME_APP_NAME) / "log"),
            str(platformdirs.user_cache_path(LEGACY_APP_NAME) / "log"),
        )
    else:
        log_dir = _resolve_runtime_path(
            platformdirs.user_log_dir(TRUST_ME_APP_NAME),
            platformdirs.user_log_dir(LEGACY_APP_NAME),
        )
    return os.path.join(log_dir, module_name) if module_name else log_dir
