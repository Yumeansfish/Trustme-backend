# Settings Schema

## Goal
Dashboard-relevant settings are normalized and validated on the backend before they are stored or used by warmup, invalidation, and DTO generation.

## Canonical keys
- `startOfDay`
- `startOfWeek`
- `durationDefault`
- `useColorFallback`
- `landingpage`
- `theme`
- `always_active_pattern`
- `classes`
- `categorizationKnowledgebaseVersion`
- `showYearly`
- `useMultidevice`
- `requestTimeout`
- `deviceMappings`

## Aliases and migration
- Legacy `alwaysActivePattern` is migrated to canonical `always_active_pattern`
- Stored settings carry `_schema_version`
- Loading settings normalizes missing keys, invalid legacy values, and aliases into the current schema

## Validation behavior
- Runtime updates to canonical dashboard keys are validated strictly
- Invalid persisted values are repaired to backend-owned defaults during load
- Unknown keys are preserved so non-dashboard settings do not break

## Defaults ownership
- Backend owns the current defaults for dashboard-relevant settings
- Backend also owns the seeded default category taxonomy used when no persisted classes exist

## Invalidation coupling
- Snapshot invalidation compares validated canonical setting values
- Formatting-only updates like `9:00` -> `09:00` do not trigger invalidation
