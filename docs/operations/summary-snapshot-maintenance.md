# Summary Snapshot Maintenance

## Purpose

This document describes the supported maintenance workflow for dashboard summary
snapshots.

## Script

Use:

- `scripts/manage_summary_snapshots.py`

The script supports:

- `inspect`
- `clear`
- `warmup`
- `rebuild`

## Examples

Inspect the most recent stored segments:

```bash
./.venv/bin/python scripts/manage_summary_snapshots.py inspect
```

Inspect only yearly segments:

```bash
./.venv/bin/python scripts/manage_summary_snapshots.py inspect --period year
```

Clear all stored segments:

```bash
./.venv/bin/python scripts/manage_summary_snapshots.py clear
```

Clear only yearly segments:

```bash
./.venv/bin/python scripts/manage_summary_snapshots.py clear --period year
```

Warm standard dashboard snapshots:

```bash
./.venv/bin/python scripts/manage_summary_snapshots.py warmup
```

Warm only a subset of periods:

```bash
./.venv/bin/python scripts/manage_summary_snapshots.py warmup --period year --period month
```

Rebuild yearly and monthly snapshots:

```bash
./.venv/bin/python scripts/manage_summary_snapshots.py rebuild --period year --period month
```

## Operational guidance

- Use `warmup` for proactive cache population.
- Use `clear` when cached state is known to be obsolete.
- Use `rebuild` after seeded-data imports or historical backfills.
- Prefer targeted logical-period clears over full-store deletion when possible.
- See [Seeded Data Workflow](./seeded-data-workflow.md) for the supported
  import-and-rebuild path.

## Notes

- Snapshot storage remains backend-internal materialization, not a source of
  truth.
- Raw buckets remain authoritative.
- Clearing or rebuilding snapshots must never be treated as a data-loss event.
