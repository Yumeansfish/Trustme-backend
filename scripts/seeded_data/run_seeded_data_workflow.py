#!/usr/bin/env python3

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_PERIODS = ("year", "month", "week")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the explicit seeded-data import workflow and optional summary snapshot rebuild.",
    )
    parser.add_argument(
        "--server-url",
        default="http://127.0.0.1:5600/api/0",
        help="Target Trust-me-compatible dashboard API base URL",
    )
    parser.add_argument(
        "--demo-marker",
        default="trustme-demo-2026",
        help="Marker stored on generated events so they can be replaced safely",
    )
    parser.add_argument(
        "--start-date",
        default="2026-01-01",
        help="First local date to seed (YYYY-MM-DD)",
    )
    parser.add_argument(
        "--end-date",
        default="2026-03-18",
        help="Last local date to seed (YYYY-MM-DD)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=20260315,
        help="Deterministic random seed used for repeatable output",
    )
    parser.add_argument(
        "--period",
        action="append",
        dest="periods",
        default=[],
        help="Logical periods to rebuild after seeding (repeatable)",
    )
    parser.add_argument(
        "--group",
        action="append",
        dest="groups",
        default=[],
        help="Optional device groups to warm during rebuild (repeatable)",
    )
    parser.add_argument(
        "--testing",
        action="store_true",
        help="Pass through testing storage mode to snapshot tooling",
    )
    parser.add_argument(
        "--storage",
        default="",
        help="Optional storage backend override for snapshot tooling",
    )
    parser.add_argument(
        "--skip-rebuild",
        action="store_true",
        help="Only seed data and skip summary snapshot rebuild",
    )
    return parser.parse_args()


def run_command(cmd: list[str]) -> None:
    subprocess.run(cmd, check=True, cwd=REPO_ROOT)


def main() -> None:
    args = parse_args()
    periods = args.periods or list(DEFAULT_PERIODS)

    generate_cmd = [
        sys.executable,
        str(REPO_ROOT / "scripts/seeded_data/generate_2026_demo_data.py"),
        "--server-url",
        args.server_url,
        "--demo-marker",
        args.demo_marker,
        "--start-date",
        args.start_date,
        "--end-date",
        args.end_date,
        "--seed",
        str(args.seed),
    ]
    run_command(generate_cmd)

    if args.skip_rebuild:
        return

    rebuild_cmd = [
        sys.executable,
        str(REPO_ROOT / "scripts/manage_summary_snapshots.py"),
        "rebuild",
    ]
    if args.testing:
        rebuild_cmd.append("--testing")
    if args.storage:
        rebuild_cmd.extend(["--storage", args.storage])
    for period in periods:
        rebuild_cmd.extend(["--period", period])
    for group in args.groups:
        rebuild_cmd.extend(["--group", group])

    run_command(rebuild_cmd)


if __name__ == "__main__":
    main()
