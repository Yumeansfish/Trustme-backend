# Dashboard DTO Contracts

## Purpose

This document defines the dashboard-facing DTOs that the frontend is expected to
consume as stable contracts.

The code-level typed representations live in:

- `aw_server/dashboard_dto.py`

## Summary snapshot contract

Endpoint:

- `POST /api/0/dashboard/summary-snapshot`

Top-level response shape:

- `window`
- `by_period`
- `uncategorized_rows`

### `window`

`window` contains aggregate events for the requested execution range.

Fields:

- `app_events`
- `title_events`
- `cat_events`
- `active_events`
- `duration`

Contract notes:

- `duration` is stable and backend-owned.
- `app_events`, `title_events`, and `cat_events` are presentation-ready
  aggregates.
- `active_events` currently exists in the response shape but should still be
  treated as backend-owned output rather than reconstructed client-side.

### `by_period`

`by_period` is a map keyed by logical period name such as:

- `day`
- `week`
- `month`
- `year`

Each value contains:

- `cat_events`

Contract notes:

- The frontend may render these period buckets directly.
- The frontend must not infer snapshot scope or internal caching behavior from
  this structure.

### `uncategorized_rows`

Each row contains:

- `key`
- `app`
- `title`
- `subtitle`
- `duration`
- `matchText`

Contract notes:

- Rows are backend-owned candidates for uncategorized management.
- The frontend may page, sort, and interact with them, but should not rebuild
  them from raw data when the DTO is available.

## Check-ins contract

Endpoint:

- `GET /api/0/dashboard/checkins`

Top-level response shape:

- `data_source`
- `available_dates`
- `sessions`

### `sessions`

Each session contains:

- `id`
- `date`
- `started_at`
- `ended_at`
- `timeline_start`
- `timeline_end`
- `duration_seconds`
- `kind`
- `answered_count`
- `skipped_count`
- `answers`

Each answer contains:

- `question_id`
- `emoji`
- `label`
- `status`
- `value`
- `value_label`
- `progress`

Contract notes:

- `available_dates` is the frontend-facing source for calendar availability.
- The frontend should not infer date availability from currently filtered
  sessions alone.
- Session grouping and answer normalization are backend-owned behavior.

## Stable vs internal

Stable frontend contract:

- Top-level DTO keys
- Nested field names documented above
- Semantic meaning of counts, durations, and availability lists

Backend-internal implementation detail:

- Snapshot scope hashing
- Segment persistence layout
- Cache invalidation strategy
- Delta-merge implementation
- Raw bucket selection heuristics used to construct the DTO

## Current consumer expectation

The frontend should behave as a DTO consumer:

- Request backend data
- Render backend-owned semantics
- Keep only interaction and presentation state locally

If a required field is missing from these DTOs, the preferred fix is to extend
the backend contract rather than rebuilding semantics in the frontend.
