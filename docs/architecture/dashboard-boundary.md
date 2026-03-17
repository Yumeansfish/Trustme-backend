# Dashboard Data Boundary

## Purpose

This document defines the stable boundary between raw bucket storage, backend
materialization, and frontend presentation logic for the dashboard stack.

## Source of truth

The only durable source of truth is raw bucket/event storage.

- Buckets identify a producer, host, and event type.
- Events carry timestamp, duration, and payload data.
- Raw buckets remain the authoritative record for replay, import, export, and
  recomputation.

Frontend-local state, seeded data, and rendered UI state are never sources of
truth.

## Backend-owned layers

### Domain semantics

The backend owns all dashboard business rules derived from raw buckets,
including:

- Device grouping
- Category application
- Active time rules
- Stopwatch/manual away semantics
- Period normalization for summary output
- Uncategorized extraction

These rules may depend on settings, but they must not be reimplemented in the
frontend.

### Materialization and snapshots

Summary snapshots are backend-internal materializations used for performance.

- They are not a second source of truth.
- They may be persisted.
- They may be rebuilt or invalidated.
- They must always be reproducible from raw buckets plus backend settings.

The frontend must not depend on internal snapshot layout or invalidation
strategy.

### DTO/API contract

The backend exposes dashboard-facing DTOs. Today the stable dashboard endpoints
are:

- `POST /api/0/dashboard/summary-snapshot`
- `GET /api/0/dashboard/checkins`
- settings endpoints for backend-owned configuration

Direct bucket and query endpoints remain backend primitives and debugging tools,
not the preferred long-term dashboard contract for rendering.

## Frontend-owned layers

The frontend owns:

- View routing
- Pagination
- Tab selection
- Hover and highlight state
- Dialog state
- Form input state
- Theme selection and presentation-only preferences

The frontend must not own:

- Summary aggregation
- Category application rules
- Stopwatch/active-time business semantics
- Period-specific materialization rules
- Cross-period cache invalidation rules

## Practical rule

When a dashboard value can affect correctness outside the current browser tab,
it belongs to the backend.

When a dashboard value only affects local rendering or interaction, it belongs
to the frontend.

## Implications for follow-up work

- Frontend summary views should consume DTOs, not reconstruct business meaning
  from raw buckets.
- Backend refactors should converge toward a service layer above raw buckets.
- Snapshot changes must preserve the DTO contract while remaining backend
  implementation detail.
