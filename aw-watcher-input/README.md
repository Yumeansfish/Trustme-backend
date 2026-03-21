# aw-watcher-input

Keyboard and mouse activity watcher for Trust-me.

This watcher records aggregate input activity only. It does not capture which
keys were pressed, and it is not intended to become a keylogger.

## Local development

Install from the module root:

```sh
poetry install
```

Run the CLI:

```sh
poetry run aw-watcher-input --help
```

## Visualization

The `visualization/` folder is still an experimental custom visualization
surface. Keep treating it as optional developer tooling rather than a supported
Trust-me product feature.
