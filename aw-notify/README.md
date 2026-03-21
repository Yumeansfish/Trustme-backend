# aw-notify-rs

Desktop notification helper for Trust-me time summaries.

This crate stays in the backend workspace and talks to a running Trust-me server
to surface check-ins, threshold alerts, and server-status notifications.

## Local development

Build from the backend workspace root:

```bash
cargo build --release -p aw-notify-rs
```

Run the service:

```bash
./target/release/aw-notify start
```

Use `aw-notify --help` for the supported command surface.

## Notes

- The maintained release surface for Trust-me is documented at the top level of
  this repository.
- This crate remains compatible with the existing category hierarchy and
  check-in flows used by the rest of the backend workspace.
