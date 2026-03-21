# Dashboard Test Lane

This is the smallest backend test lane that is worth keeping green while the
dashboard refactor is still moving.

It is intentionally narrower than the full backend suite:

- it only covers dashboard-focused unit and route tests
- it does not depend on the legacy `tests/conftest.py` bootstrap
- it is meant to run from a clean checkout with one command

## Command

From the backend repo root:

```bash
make test-dashboard
```

What that command does:

- creates or reuses `backend/.venv-dashboard-tests`
- installs local editable copies of `aw-core`, `aw-client`, and `aw-server`
- runs the dashboard-focused pytest subset with `--noconftest`

## Covered tests

The current dashboard lane runs:

- `aw-server/tests/test_dashboard_details.py`
- `aw-server/tests/test_dashboard_domain_service.py`
- `aw-server/tests/test_dashboard_dto.py`
- `aw-server/tests/test_summary_snapshot_response.py`
- `aw-server/tests/test_dashboard_routes.py`

This is the preferred first stop when changing:

- dashboard DTO shapes
- scope resolution
- snapshot response shaping
- dashboard route contracts
- browser / stopwatch dashboard summaries

## Re-bootstrap

If you need to force a fresh environment install:

```bash
FORCE_BOOTSTRAP=1 make test-dashboard
```

## Why this lane exists

The full backend suite still carries older bootstrap assumptions that are not a
good fit for the current frontend/backend split work.

This lane gives the refactor a stable, small signal first. Broader test cleanup
can continue separately without blocking dashboard work.
