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

The actively maintained release path is the Trust-me-owned GitHub Actions build
workflow plus the packaging helpers it still invokes directly. Manual Linux
packaging helpers that are merely present in `package/` should not be assumed
to be part of the current supported CI path unless they are wired into that
workflow.

Legacy standalone Linux packaging helpers have been retired from this repo's
supported surface. If Linux release automation returns, it should be rebuilt
around the current Trust-me packaging path instead of reviving the old
ActivityWatch-era scripts.

Legacy Windows installer helpers have also been retired. If Windows packaging
returns, it should be rebuilt around the current Trust-me release flow instead
of reviving the old Inno Setup path.

## Historical cleanup boundary

Inherited ActivityWatch release automation is tracked separately from this
README cleanup. The goal here is simply to keep clearly supported utilities
distinguishable from unsupported leftovers.

Root-level install, uninstall, log scraping, and line-count shortcuts are not a
supported surface here anymore. If an operator workflow still matters, it
should live with the owning module or be documented under `docs/operations/`.
