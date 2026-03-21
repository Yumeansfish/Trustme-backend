# Awatcher

Linux activity and idle watcher for Trust-me.

`awatcher` exists in this workspace as an optional replacement for the separate
window and AFK watchers on Linux. It can run as a standalone watcher module or
be built with extra bundle features for local packaging experiments.

## Scope

- Linux only
- Active window detection plus idle detection
- Optional tray and bundled-server features behind Cargo feature flags

## Local development

Build from the module root:

```bash
cargo build --release
```

The binary will be available at `target/release/awatcher`.

Use `cargo run -- --help` for the current command surface.

## Notes

- The maintained Trust-me release path is documented at the top level of the
  backend repository.
- Compatibility-oriented package names such as `aw-awatcher` are still retained
  where packaging metadata depends on them.
