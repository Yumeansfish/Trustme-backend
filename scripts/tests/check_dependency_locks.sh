#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

if ! command -v cargo >/dev/null 2>&1; then
  echo "cargo is required for Rust lockfile checks" >&2
  exit 1
fi

for manifest in \
  "aw-notify/Cargo.toml" \
  "aw-tauri/src-tauri/Cargo.toml" \
  "awatcher/Cargo.toml"
do
  cargo metadata --locked --manifest-path "${ROOT_DIR}/${manifest}" --format-version 1 >/dev/null
done

if command -v poetry >/dev/null 2>&1; then
  (
    cd "${ROOT_DIR}/aw-watcher-input"
    poetry check >/dev/null
  )
elif command -v uv >/dev/null 2>&1; then
  (
    cd "${ROOT_DIR}/aw-watcher-input"
    uv tool run --from poetry==1.8.3 poetry check >/dev/null
  )
else
  echo "poetry or uv is required for aw-watcher-input checks" >&2
  exit 1
fi

echo "Dependency lock/config checks passed."
