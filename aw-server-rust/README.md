aw-server-rust
==============

Rust server components used by the Trust-me backend workspace.

## Build

With Cargo:

```sh
cargo build --release
```

Or through the repo-level build after preparing frontend assets:

```sh
make -C .. prepare-frontend FRONTEND_DIR=../frontend
make build
```

`aw-server-rust` consumes a built frontend artifact from
`../build/frontend-artifact` by default. Set `AW_WEBUI_DIR=/absolute/path/to/dist`
if you want to point it at a different frontend build output.

## Run

For a quick local run:

```sh
cargo run --bin aw-server
```

That starts the Rust server in testing mode.

## Sync

See [aw-sync/README.md](./aw-sync/README.md) for sync-specific details.
