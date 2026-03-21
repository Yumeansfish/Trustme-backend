# aw-sync

Folder-based synchronization support for the Trust-me Rust workspace.

This crate is still an internal tool. It mirrors selected buckets through a sync
directory that can then be replicated with Syncthing, Dropbox, rsync, or similar
tools.

## Usage

Run the daemon:

```sh
aw-sync
```

For development from source:

```sh
cargo run --bin aw-sync
```

Use `aw-sync --help` or `cargo run --bin aw-sync -- --help` for the full option
list.

## Notes

- Fresh installs now default to `~/TrustMeSync`.
- If an existing `~/ActivityWatchSync` directory is already present and no
  Trust-me sync root exists yet, `aw-sync` will keep using the legacy path
  automatically.
- The currently maintained release path for Trust-me is documented in the top-level
  backend README and workflow files.
- Treat this crate as workspace-internal unless Trust-me explicitly documents a
  supported sync product surface later.
