# Dashboard Domain Service

## Purpose
The dashboard domain service sits above raw bucket metadata and below DTO builders. Its job is to turn generic bucket storage plus normalized settings into stable dashboard semantics.

## Responsibilities
- Build bucket-record views from raw bucket metadata
- Resolve effective device groups from known hosts and backend-owned `deviceMappings`
- Apply dashboard categorization semantics from backend-owned `classes`
- Resolve active-time semantics such as `filter_afk` and `always_active_pattern`
- Resolve stopwatch semantics, including unknown-host fallback selection
- Produce semantic summary scopes that downstream DTO builders can consume

## Non-responsibilities
- It does not build final summary aggregates
- It does not serialize API responses
- It does not persist snapshots directly

## Current consumers
- Summary warmup job construction
- Snapshot invalidation target construction
- Ad-hoc summary DTO requests routed through `ServerAPI.summary_snapshot`

## Design intent
Future dashboard features should depend on semantic scopes from this layer rather than reproducing host grouping, bucket selection, or category translation in endpoints or frontend code.
