aw-server
=========

Python dashboard server used in the Trust-me backend workspace.

## Build

Prepare frontend assets first:

```bash
make -C .. prepare-frontend FRONTEND_DIR=../frontend
```

Then build the server:

```bash
make build
```

`aw-server` consumes built frontend assets from `../build/frontend-artifact` by
default. Set `AW_WEBUI_DIR=/absolute/path/to/dist` if you want to point it at a
different frontend build output.

## Run

```bash
aw-server
```

For an isolated development instance:

```bash
aw-server --testing
```

## Notes

- This module remains part of the Trust-me packaging workspace.
- Dashboard DTO and summary-snapshot work is owned in this repository rather
  than in the old upstream monorepo docs.
