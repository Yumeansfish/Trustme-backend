# Frontend Artifact Contract

Backend-side targets now consume one frontend artifact layout instead of carrying their own embedded
frontend source trees.

## Default location

- `build/frontend-artifact`

You can override this by setting `AW_WEBUI_DIR` to an absolute path.

## How to build it

From the backend repo root:

```sh
make prepare-frontend FRONTEND_DIR=../frontend
```

That command builds the standalone frontend repo and syncs its `dist/` output into the artifact
directory.

## How targets consume it

- `aw-server` copies the artifact into `aw_server/static/` before packaging.
- `aw-server-rust` embeds the artifact at compile time.
- `aw-tauri` points both the Tauri build and the bundled Rust server at the same artifact.

## Meaning of `SKIP_WEBUI`

`SKIP_WEBUI=true` skips artifact generation.

It does not switch targets back to an alternate source layout. If you skip generation, the target is
expected to consume an artifact that already exists at `AW_WEBUI_DIR`.
