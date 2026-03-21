# Contributing

Trust-me is no longer developed as the upstream ActivityWatch monorepo. This
repository should use its own issue tracker, release flow, and contribution
rules.

## Before you start

- use this repository's issues for backend work that belongs to Trust-me
- keep changes scoped to the problem you are solving
- prefer small, reviewable pull requests over broad mixed refactors

## Local verification

Run the smallest relevant verification you can before sending changes:

- `make test-dashboard` for the backend dashboard contract and route subset
- `make build SKIP_WEBUI=true` when changing backend packaging or runtime build behavior
- targeted module tests when working inside a specific subproject

If a change depends on frontend artifacts, use the documented frontend sync path
instead of reintroducing bundled web UI source copies.

## Commit messages

Conventional Commits are encouraged:

```text
<type>[optional scope]: <description>
```

Typical types in this repo:

- `feat`
- `fix`
- `refactor`
- `docs`
- `test`
- `ci`
- `build`
- `cleanup`

## Code of Conduct

Follow [`CODE_OF_CONDUCT.md`](./CODE_OF_CONDUCT.md).

## Questions

If something is unclear, open an issue in this repository with enough context
to show what area of the Trust-me backend you are touching and what behavior
you expect to preserve.
