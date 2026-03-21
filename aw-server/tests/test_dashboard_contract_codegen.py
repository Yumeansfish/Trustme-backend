from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[2]
SCRIPT_PATH = ROOT_DIR / "scripts" / "contracts" / "export_dashboard_contract_ts.py"


def test_dashboard_contract_codegen_exports_expected_interfaces():
    result = subprocess.run(
        [sys.executable, str(SCRIPT_PATH)],
        check=True,
        capture_output=True,
        text=True,
    )

    output = result.stdout
    assert "export interface SummarySnapshotResponse {" in output
    assert "by_period: Record<string, SummaryByPeriodEntry>;" in output
    assert '"$category"?: string[];' in output
    assert "progress: number | null;" in output
    assert "export interface DashboardScopeResponse {" in output
