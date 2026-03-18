# Seeded Data Tooling

This directory contains non-runtime utilities for seeded-data workflows.

These scripts are intentionally separate from the backend runtime:

- runtime services must not import or depend on this directory
- seeded-data imports are explicit operator actions
- summary snapshot rebuilds happen through maintenance tooling, not hidden runtime hooks

## Available scripts

- `generate_2026_demo_data.py`
  - generates reproducible 2026 dashboard data against a local ActivityWatch-compatible API
- `run_seeded_data_workflow.py`
  - runs the seeded-data import and then rebuilds the relevant summary snapshots

## Typical usage

```bash
./.venv/bin/python scripts/seeded_data/run_seeded_data_workflow.py
```

This seeds 2026 data and rebuilds the standard `year`, `month`, and `week`
summary snapshots.

If you only want to refresh the seeded bucket events:

```bash
./.venv/bin/python scripts/seeded_data/generate_2026_demo_data.py
```
