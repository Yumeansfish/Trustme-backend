# Script Ownership

This directory contains maintenance and packaging utilities for the backend
repo. It is not part of the runtime application surface.

## Supported utility paths

- `contracts/`
  Dashboard contract code generation used by the frontend/backend split.
- `release/`
  Release-time helpers such as syncing a built frontend artifact into the
  backend packaging tree.
- `seeded_data/`
  Explicit operator tooling for deterministic demo/seed imports.
- `tests/`
  Targeted backend test runners such as the dashboard subset lane.
- `manage_summary_snapshots.py`
  Supported snapshot maintenance utility.

## Packaging and CI helpers

- `package/`

These scripts support packaging environments. They are not runtime
dependencies, but they are intentionally kept while the packaging surface
exists.

## Historical cleanup boundary

Inherited ActivityWatch release automation is tracked separately from this
README cleanup. The goal here is simply to keep clearly supported utilities
distinguishable from unsupported leftovers.

Root-level install, uninstall, log scraping, and line-count shortcuts are not a
supported surface here anymore. If an operator workflow still matters, it
should live with the owning module or be documented under `docs/operations/`.
