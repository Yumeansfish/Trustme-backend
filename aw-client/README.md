# aw-client

Python client helpers for Trust-me services.

This package stays in the backend workspace to support local tooling, scripts,
and compatible watcher/server integrations. The supported product surface for
Trust-me is documented from the top-level backend README and workflows.

For local development:

```sh
poetry install
```

The package still exposes the `aw-client` CLI for bucket inspection, heartbeats,
queries, and report-oriented debugging against a running Trust-me server.
