#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import math
import random
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from pathlib import Path
from collections import deque
from typing import Dict, Iterable, List, Sequence
from zoneinfo import ZoneInfo


TIMEZONE = ZoneInfo("Europe/Zurich")
DEFAULT_SERVER_URL = "http://127.0.0.1:5600/api/0"
DEFAULT_DEMO_MARKER = "trustme-demo-2026"
DEFAULT_START_DAY = date(2026, 1, 1)
DEFAULT_RANDOM_SEED = 20260315

EDITOR_BUCKET = "aw-watcher-vscode_USILU-16193.local"
WINDOW_BUCKET = "aw-watcher-window_USILU-16193.local"
AFK_BUCKET = "aw-watcher-afk_USILU-16193.local"


@dataclass(frozen=True)
class ProjectSpec:
    key: str
    label: str
    project_path: str
    roots: Sequence[Path]
    ignored_dirs: Sequence[str]
    allowed_suffixes: Sequence[str]


PROJECTS: Sequence[ProjectSpec] = (
    ProjectSpec(
        key="in_context_scheming",
        label="in-context-scheming",
        project_path="/Users/usi/Desktop/in-context-scheming-env",
        roots=(Path("/Users/usi/Desktop/in-context-scheming-env"),),
        ignored_dirs=("__pycache__", ".git", ".venv", "venv", "build", ".ipynb_checkpoints"),
        allowed_suffixes=(
            ".py",
            ".yml",
            ".yaml",
            ".md",
            ".ipynb",
            ".json",
            ".sh",
            ".log",
        ),
    ),
    ProjectSpec(
        key="trust_me",
        label="trust-me",
        project_path="/Users/usi/Desktop/trust-me",
        roots=(Path("/Users/usi/Desktop/trust-me"),),
        ignored_dirs=(
            "node_modules",
            ".git",
            "dist",
            "static",
            "__pycache__",
            "build",
            "target",
            "backups",
            "venv",
            ".venv",
        ),
        allowed_suffixes=(
            ".ts",
            ".tsx",
            ".js",
            ".jsx",
            ".vue",
            ".py",
            ".rs",
            ".json",
            ".md",
            ".css",
            ".scss",
            ".html",
        ),
    ),
    ProjectSpec(
        key="project211",
        label="project211",
        project_path="/Users/usi/Desktop/project211",
        roots=(Path("/Users/usi/Desktop/project211"),),
        ignored_dirs=("eval_checkpoints", ".git", "__pycache__", "build"),
        allowed_suffixes=(
            ".py",
            ".sh",
            ".md",
            ".yaml",
            ".yml",
            ".json",
            ".jsonl",
            ".html",
        ),
    ),
)


LANGUAGE_BY_SUFFIX = {
    ".py": "python",
    ".ts": "typescript",
    ".tsx": "typescriptreact",
    ".js": "javascript",
    ".jsx": "javascriptreact",
    ".vue": "vue",
    ".rs": "rust",
    ".json": "json",
    ".jsonl": "json",
    ".yml": "yaml",
    ".yaml": "yaml",
    ".md": "markdown",
    ".css": "css",
    ".scss": "scss",
    ".html": "html",
    ".sh": "shellscript",
    ".ipynb": "jupyter",
    ".log": "log",
}


NON_CODE_ACTIVITY_SPECS = (
    {
        "app": "Firefox",
        "titles": (
            "Trust-me dashboard notes — Firefox",
            "Activity design references — Firefox",
            "Swiss NLP paper reading — Firefox",
            "Figma plugin docs — Firefox",
            "Research browser tab cleanup — Firefox",
        ),
        "min_minutes": 12,
        "max_minutes": 36,
        "daily_probability": 0.92,
    },
    {
        "app": "Figma",
        "titles": (
            "Trust-me activity redesign",
            "Check-ins card layout",
            "Privacy control exploration",
            "Summary pie chart polish",
            "Raw data card system",
        ),
        "min_minutes": 10,
        "max_minutes": 28,
        "daily_probability": 0.42,
    },
    {
        "app": "League Of Legends",
        "titles": (
            "League Client",
            "Ranked Solo Queue",
            "Champion Select",
            "ARAM Queue",
        ),
        "min_minutes": 18,
        "max_minutes": 42,
        "daily_probability": 0.28,
    },
)


PRIMARY_EDITOR_SUFFIXES = {
    ".py",
    ".ts",
    ".tsx",
    ".js",
    ".jsx",
    ".vue",
    ".rs",
    ".ipynb",
}

EDITOR_SUFFIX_WEIGHTS = {
    ".py": 1.0,
    ".ts": 1.0,
    ".tsx": 0.95,
    ".js": 0.92,
    ".jsx": 0.9,
    ".vue": 1.08,
    ".rs": 0.72,
    ".ipynb": 0.28,
    ".sh": 0.18,
    ".css": 0.08,
    ".scss": 0.08,
    ".md": 0.03,
    ".json": 0.02,
    ".jsonl": 0.02,
    ".log": 0.01,
    ".yml": 0.01,
    ".yaml": 0.01,
    ".html": 0.01,
}

LOW_SIGNAL_PATH_PARTS = {
    "config",
    "configs",
    "settings",
    "static",
    "assets",
    "dist",
    "build",
    "coverage",
    "dataset",
    "datasets",
    "logs",
    "log",
    "trainset",
    "testset",
    "pool",
    "scenarios",
}

LOW_SIGNAL_FILENAMES = {
    "package.json",
    "package-lock.json",
    "pnpm-lock.yaml",
    "yarn.lock",
    "tsconfig.json",
    "vite.config.ts",
    "vite.config.js",
    "tailwind.config.ts",
    "tailwind.config.js",
    "pyproject.toml",
    "poetry.lock",
    "requirements.txt",
}

PROJECT_ALLOCATION_WEIGHTS = {
    "in_context_scheming": 0.20,
    "trust_me": 0.72,
    "project211": 0.08,
}

MAX_FILE_DURATION_SECONDS = 30 * 60
RECENT_FILE_MEMORY = 7


@dataclass(frozen=True)
class SeedConfig:
    server_url: str
    demo_marker: str
    start_day: date
    end_day: date
    random_seed: int


def api_request(
    server_url: str,
    method: str,
    path: str,
    *,
    query: Dict[str, object] | None = None,
    payload: object | None = None,
) -> object:
    url = f"{server_url}{path}"
    if query:
        url += "?" + urllib.parse.urlencode(query)
    data = None
    headers = {}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(request) as response:
        body = response.read()
    return json.loads(body.decode("utf-8")) if body else None


def chunked(items: Sequence[dict], size: int) -> Iterable[Sequence[dict]]:
    for start in range(0, len(items), size):
        yield items[start : start + size]


def collect_project_files(project: ProjectSpec) -> List[Path]:
    allowed = {suffix.lower() for suffix in project.allowed_suffixes}
    ignored = set(project.ignored_dirs)
    files: List[Path] = []
    for root in project.roots:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if not path.is_file():
                continue
            if any(part in ignored for part in path.parts):
                continue
            if path.suffix.lower() not in allowed:
                continue
            files.append(path)
    return sorted(set(files))


def allocate_minutes(
    randomizer: random.Random,
    total_minutes: int,
    projects: Sequence[ProjectSpec],
) -> Dict[str, int]:
    minimums = {project.key: 10 for project in projects}
    remainder = total_minutes - sum(minimums.values())
    if remainder < 0:
        raise ValueError("total_minutes too small")

    jittered_weights = {
        project.key: PROJECT_ALLOCATION_WEIGHTS[project.key] * randomizer.uniform(0.7, 1.35)
        for project in projects
    }
    weight_sum = sum(jittered_weights.values())
    raw = {
        project.key: minimums[project.key] + remainder * jittered_weights[project.key] / weight_sum
        for project in projects
    }
    rounded = {
        project.key: max(minimums[project.key], int(round(value / 5.0) * 5))
        for project, value in ((project, raw[project.key]) for project in projects)
    }

    diff = total_minutes - sum(rounded.values())
    keys = [project.key for project in projects]
    while diff != 0:
        if diff > 0:
            key = randomizer.choice(keys)
            rounded[key] += 5
            diff -= 5
        else:
            candidates = [key for key in keys if rounded[key] - 5 >= minimums[key]]
            key = randomizer.choice(candidates)
            rounded[key] -= 5
            diff += 5

    return rounded


def select_file_pool(randomizer: random.Random, files: Sequence[Path], size: int) -> List[Path]:
    if len(files) <= size:
        return list(files)
    sampled = list(files)
    randomizer.shuffle(sampled)
    return sampled[:size]


def split_editor_file_tiers(files: Sequence[Path]) -> tuple[List[Path], List[Path]]:
    primary = [path for path in files if path.suffix.lower() in PRIMARY_EDITOR_SUFFIXES]
    secondary = [path for path in files if path.suffix.lower() not in PRIMARY_EDITOR_SUFFIXES]
    return primary, secondary


def editor_file_weight(path: Path) -> float:
    weight = EDITOR_SUFFIX_WEIGHTS.get(path.suffix.lower(), 0.01)
    parts = {part.lower() for part in path.parts}
    if parts & LOW_SIGNAL_PATH_PARTS:
        weight *= 0.08
    if path.name.lower() in LOW_SIGNAL_FILENAMES:
        weight *= 0.04
    if path.stem.lower() in {"index", "main", "app"}:
        weight *= 1.08
    return max(weight, 0.001)


def weighted_choice(randomizer: random.Random, files: Sequence[Path]) -> Path:
    return randomizer.choices(
        list(files),
        weights=[editor_file_weight(path) for path in files],
        k=1,
    )[0]


def select_hot_files(randomizer: random.Random, files: Sequence[Path], size: int) -> List[Path]:
    if len(files) <= size:
        return list(files)

    selected: List[Path] = []
    remaining = list(files)
    while remaining and len(selected) < size:
        choice = weighted_choice(randomizer, remaining)
        selected.append(choice)
        remaining.remove(choice)
    return selected


def build_file_cycle(randomizer: random.Random, files: Sequence[Path]) -> deque[Path]:
    ordered = list(files)
    randomizer.shuffle(ordered)
    return deque(ordered)


def choose_file(
    randomizer: random.Random,
    primary_cycle: deque[Path],
    secondary_cycle: deque[Path],
    file_duration_totals: Dict[str, float],
    recent_files: Sequence[str],
) -> Path:
    recent_file_set = set(recent_files)

    def pull_from_cycle(
        cycle: deque[Path],
        *,
        enforce_cap: bool,
        avoid_recent: bool,
    ) -> Path | None:
        if not cycle:
            return None
        for _ in range(len(cycle)):
            candidate = cycle[0]
            cycle.rotate(-1)
            candidate_key = str(candidate)
            if enforce_cap and file_duration_totals.get(candidate_key, 0.0) >= MAX_FILE_DURATION_SECONDS:
                continue
            if avoid_recent and candidate_key in recent_file_set:
                continue
            return candidate
        return None

    prefer_primary = randomizer.random() < 0.94 or not secondary_cycle
    ordered_cycles = (
        (primary_cycle, secondary_cycle)
        if prefer_primary
        else (secondary_cycle, primary_cycle)
    )

    for cycle in ordered_cycles:
        candidate = pull_from_cycle(cycle, enforce_cap=True, avoid_recent=True)
        if candidate is not None:
            return candidate
    for cycle in ordered_cycles:
        candidate = pull_from_cycle(cycle, enforce_cap=True, avoid_recent=False)
        if candidate is not None:
            return candidate
    for cycle in ordered_cycles:
        candidate = pull_from_cycle(cycle, enforce_cap=False, avoid_recent=True)
        if candidate is not None:
            return candidate
    for cycle in ordered_cycles:
        candidate = pull_from_cycle(cycle, enforce_cap=False, avoid_recent=False)
        if candidate is not None:
            return candidate

    raise RuntimeError("No files available for demo event generation")


def language_for_file(path: Path) -> str:
    return LANGUAGE_BY_SUFFIX.get(path.suffix.lower(), "plaintext")


def isoformat_with_ms(value: datetime) -> str:
    return value.isoformat(timespec="milliseconds")


def project_window_title(file_path: Path, project_label: str) -> str:
    return f"{file_path.name} — {project_label}"


def build_non_code_window_events(
    randomizer: random.Random,
    cursor: datetime,
    demo_marker: str,
) -> List[dict]:
    events: List[dict] = []
    block_cursor = cursor + timedelta(minutes=randomizer.randint(6, 24))

    for spec in NON_CODE_ACTIVITY_SPECS:
        if randomizer.random() > spec["daily_probability"]:
            continue

        minutes = randomizer.randint(spec["min_minutes"], spec["max_minutes"])
        minutes = int(round(minutes / 2.0) * 2)
        if minutes <= 0:
            continue

        started_at = block_cursor
        duration_seconds = minutes * 60
        events.append(
            {
                "timestamp": isoformat_with_ms(started_at),
                "duration": duration_seconds,
                "data": {
                    "app": spec["app"],
                    "title": randomizer.choice(spec["titles"]),
                    "demo_source": demo_marker,
                },
            }
        )
        block_cursor = started_at + timedelta(seconds=duration_seconds) + timedelta(
            minutes=randomizer.randint(4, 18)
        )

    return events


def clear_existing_demo_events(
    config: SeedConfig,
    bucket_id: str,
    start: datetime,
    end: datetime,
) -> int:
    events = api_request(
        config.server_url,
        "GET",
        f"/buckets/{bucket_id}/events",
        query={
            "limit": -1,
            "start": start.isoformat(),
            "end": end.isoformat(),
        },
    )
    deleted = 0
    for event in events or []:
        data = event.get("data") or {}
        if data.get("demo_source") != config.demo_marker:
            continue
        api_request(config.server_url, "DELETE", f"/buckets/{bucket_id}/events/{event['id']}")
        deleted += 1
    return deleted


def build_demo_events(config: SeedConfig) -> Dict[str, List[dict]]:
    randomizer = random.Random(config.random_seed)

    project_files = {
        project.key: collect_project_files(project)
        for project in PROJECTS
    }
    for project in PROJECTS:
        if not project_files[project.key]:
            raise RuntimeError(f"No files found for {project.label} at {project.project_path}")

    primary_files = {
        project.key: split_editor_file_tiers(project_files[project.key])[0]
        for project in PROJECTS
    }
    secondary_files = {
        project.key: split_editor_file_tiers(project_files[project.key])[1]
        for project in PROJECTS
    }

    primary_cycles = {
        project.key: build_file_cycle(
            randomizer,
            primary_files[project.key] or project_files[project.key],
        )
        for project in PROJECTS
    }
    secondary_cycles = {
        project.key: build_file_cycle(randomizer, secondary_files[project.key])
        for project in PROJECTS
    }
    file_duration_totals: Dict[str, float] = {}
    recent_files_by_project = {
        project.key: deque(maxlen=RECENT_FILE_MEMORY)
        for project in PROJECTS
    }

    editor_events: List[dict] = []
    window_events: List[dict] = []
    afk_events: List[dict] = []

    current_day = config.start_day
    while current_day <= config.end_day:
        total_minutes = randomizer.randrange(180, 361, 15)
        allocations = allocate_minutes(randomizer, total_minutes, PROJECTS)

        session_order = [(project, allocations[project.key]) for project in PROJECTS]
        randomizer.shuffle(session_order)

        cursor = datetime.combine(
            current_day,
            time(hour=9, minute=0),
            tzinfo=TIMEZONE,
        ) + timedelta(minutes=randomizer.randint(10, 80))

        day_first_event: datetime | None = None
        day_last_event: datetime | None = None

        for project, project_minutes in session_order:
            session_start = cursor
            remaining_minutes = project_minutes
            while remaining_minutes > 0:
                chunk_minutes = min(
                    remaining_minutes,
                    randomizer.choice((8, 10, 12, 15, 18, 20, 24, 28)),
                )
                file_path = choose_file(
                    randomizer,
                    primary_cycles[project.key],
                    secondary_cycles[project.key],
                    file_duration_totals,
                    list(recent_files_by_project[project.key]),
                )
                started_at = cursor
                duration_seconds = chunk_minutes * 60
                ended_at = started_at + timedelta(seconds=duration_seconds)

                event_data = {
                    "language": language_for_file(file_path),
                    "project": project.project_path,
                    "file": str(file_path),
                    "demo_source": config.demo_marker,
                }
                editor_events.append(
                    {
                        "timestamp": isoformat_with_ms(started_at),
                        "duration": duration_seconds,
                        "data": event_data,
                    }
                )
                window_events.append(
                    {
                        "timestamp": isoformat_with_ms(started_at),
                        "duration": duration_seconds,
                        "data": {
                            "app": "Code",
                            "title": project_window_title(file_path, project.label),
                            "demo_source": config.demo_marker,
                        },
                    }
                )

                if day_first_event is None or started_at < day_first_event:
                    day_first_event = started_at
                if day_last_event is None or ended_at > day_last_event:
                    day_last_event = ended_at
                file_duration_totals[str(file_path)] = (
                    file_duration_totals.get(str(file_path), 0.0) + duration_seconds
                )
                recent_files_by_project[project.key].append(str(file_path))

                remaining_minutes -= chunk_minutes
                cursor = ended_at + timedelta(minutes=randomizer.randint(1, 4))

            cursor = cursor + timedelta(minutes=randomizer.randint(8, 28))

        for window_event in build_non_code_window_events(randomizer, cursor, config.demo_marker):
            started_at = datetime.fromisoformat(window_event["timestamp"])
            ended_at = started_at + timedelta(seconds=window_event["duration"])
            window_events.append(window_event)

            if day_first_event is None or started_at < day_first_event:
                day_first_event = started_at
            if day_last_event is None or ended_at > day_last_event:
                day_last_event = ended_at

        if day_first_event and day_last_event and day_last_event > day_first_event:
            afk_events.append(
                {
                    "timestamp": isoformat_with_ms(day_first_event),
                    "duration": (day_last_event - day_first_event).total_seconds(),
                    "data": {
                        "status": "not-afk",
                        "demo_source": config.demo_marker,
                    },
                }
            )

        current_day += timedelta(days=1)

    editor_events.sort(key=lambda event: event["timestamp"])
    window_events.sort(key=lambda event: event["timestamp"])
    afk_events.sort(key=lambda event: event["timestamp"])

    return {
        EDITOR_BUCKET: editor_events,
        WINDOW_BUCKET: window_events,
        AFK_BUCKET: afk_events,
    }


def ensure_bucket_exists(config: SeedConfig, bucket_id: str) -> None:
    buckets = api_request(config.server_url, "GET", "/buckets")
    if bucket_id not in buckets:
        raise RuntimeError(f"Bucket {bucket_id} was not found on the local server")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate reproducible seeded dashboard data for the local 2026 walkthrough.",
    )
    parser.add_argument(
        "--server-url",
        default=DEFAULT_SERVER_URL,
        help="Target Trust-me-compatible dashboard API base URL",
    )
    parser.add_argument(
        "--demo-marker",
        default=DEFAULT_DEMO_MARKER,
        help="Marker stored on generated events so they can be replaced safely",
    )
    parser.add_argument(
        "--start-date",
        default=DEFAULT_START_DAY.isoformat(),
        help="First local date to seed (YYYY-MM-DD)",
    )
    parser.add_argument(
        "--end-date",
        default=datetime.now(TIMEZONE).date().isoformat(),
        help="Last local date to seed (YYYY-MM-DD)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=DEFAULT_RANDOM_SEED,
        help="Deterministic random seed used for repeatable output",
    )
    return parser.parse_args()


def build_seed_config(args: argparse.Namespace) -> SeedConfig:
    start_day = date.fromisoformat(args.start_date)
    end_day = date.fromisoformat(args.end_date)
    if end_day < start_day:
        raise ValueError("end-date must be on or after start-date")
    return SeedConfig(
        server_url=args.server_url.rstrip("/"),
        demo_marker=args.demo_marker,
        start_day=start_day,
        end_day=end_day,
        random_seed=args.seed,
    )


def main() -> None:
    config = build_seed_config(parse_args())

    for bucket_id in (EDITOR_BUCKET, WINDOW_BUCKET, AFK_BUCKET):
        ensure_bucket_exists(config, bucket_id)

    start = datetime.combine(config.start_day, time.min, tzinfo=TIMEZONE)
    end = datetime.combine(config.end_day, time.max, tzinfo=TIMEZONE) + timedelta(seconds=1)

    for bucket_id in (EDITOR_BUCKET, WINDOW_BUCKET, AFK_BUCKET):
        deleted = clear_existing_demo_events(config, bucket_id, start, end)
        print(f"deleted {deleted} old demo events from {bucket_id}")

    payload_by_bucket = build_demo_events(config)
    for bucket_id, events in payload_by_bucket.items():
        for batch in chunked(events, 500):
            api_request(config.server_url, "POST", f"/buckets/{bucket_id}/events", payload=list(batch))
        print(f"inserted {len(events)} demo events into {bucket_id}")


if __name__ == "__main__":
    main()
