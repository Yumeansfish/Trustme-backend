# Summary Snapshot Invalidation

## Purpose

This document explains which settings influence dashboard summary snapshot
materialization and how invalidation is scoped.

## Current rule

Snapshot invalidation is based on the previous effective warmup targets rather
than clearing the entire snapshot store.

When a dashboard-relevant setting changes, the backend:

1. Builds the warmup targets implied by the previous settings
2. Resolves their snapshot scope keys and logical periods
3. Deletes only those matching snapshot segments

This avoids deleting unrelated summary snapshot scopes.

## Setting impact map

### `classes`

Changes:

- category application
- uncategorized extraction
- aggregated category output

Affected dimensions:

- Snapshot scope key via serialized category rules

### `always_active_pattern` / `alwaysActivePattern`

Changes:

- active interval construction
- visible window slices

Affected dimensions:

- Snapshot scope key via active-time semantics

### `deviceMappings`

Changes:

- host-to-group assignment
- selected bucket lists per warmup group

Affected dimensions:

- Snapshot scope key via resolved bucket selection

### `startOfDay`

Changes:

- logical period boundaries
- warmup period anchor

Affected dimensions:

- Logical period keys

### `startOfWeek`

Changes:

- weekly logical period boundaries

Affected dimensions:

- Logical period keys for week-oriented materialization

## What is not invalidated

Unrelated scopes that are not part of the previous warmup target set are left
untouched.

This means seeded experiments, manual inspection scopes, or future specialized
materializations are not wiped unless they overlap the targeted invalidation set.
