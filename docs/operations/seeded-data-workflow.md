# Seeded Data Workflow

## Purpose

This document describes the supported workflow for importing seeded dashboard
data without mixing that behavior into the runtime backend.

## Principles

- Raw buckets remain the source of truth.
- Seeded-data utilities are explicit operator tools.
- Runtime backend code must not import or depend on seeded-data scripts.
- Snapshot rebuilds happen through maintenance commands after import.

## Tooling path

Seeded-data tooling lives under:

- `scripts/seeded_data/`

The current supported workflow scripts are:

- `scripts/seeded_data/generate_2026_demo_data.py`
- `scripts/seeded_data/run_seeded_data_workflow.py`

## Standard workflow

Run the import and rebuild workflow:

```bash
./.venv/bin/python scripts/seeded_data/run_seeded_data_workflow.py
```

By default this will:

1. regenerate the 2026 seeded events using deterministic parameters
2. replace earlier events carrying the same seeded-data marker
3. rebuild the standard `year`, `month`, and `week` summary snapshots

## Partial workflow

Import seeded events only:

```bash
./.venv/bin/python scripts/seeded_data/generate_2026_demo_data.py
```

Import seeded events and rebuild a narrower period set:

```bash
./.venv/bin/python scripts/seeded_data/run_seeded_data_workflow.py --period year --period month
```

## Snapshot handling

Seeded-data imports change historical bucket contents. They must therefore be
followed by snapshot maintenance. Use one of these approaches:

- the combined workflow script above
- `scripts/manage_summary_snapshots.py rebuild ...`

Do not rely on runtime requests to implicitly correct seeded historical data.

## Runtime separation

The backend runtime remains independent from seeded-data tooling:

- no runtime module should import `scripts/seeded_data`
- no endpoint should depend on seeded-data paths or markers
- seeded-data maintenance must remain reproducible from explicit tooling alone
