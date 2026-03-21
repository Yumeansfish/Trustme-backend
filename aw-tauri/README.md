aw-tauri
========

Tauri desktop shell used in the Trust-me backend workspace.

It consumes a built frontend artifact and bundles the desktop runtime around
the current Trust-me release flow.

## Prerequisites

- Tauri prerequisites from the official Tauri docs
- Node.js
- Rust

## Run

```sh
make -C .. prepare-frontend FRONTEND_DIR=../frontend
make dev
```

## Build

```sh
make -C .. prepare-frontend FRONTEND_DIR=../frontend
make build
```

## Repo structure

- desktop packaging lives in the repo root
- the bundled Rust app lives in `src-tauri/`
- frontend assets are consumed from a built artifact, not from an embedded
  frontend source tree
