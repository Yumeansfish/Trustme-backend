# Backend JavaScript Leftovers

The backend worktree only has two first-party JavaScript files left on purpose.

## Intentional keepers

### `awatcher/watchers/src/watchers/kwin_window.js`

- Loaded from Rust with `include_str!`
- Written to a temp file and executed by the KWin scripting engine
- Not part of the repo's normal Node/TypeScript toolchain

This is a runtime integration script, not a frontend/backend app module. It
should stay JavaScript unless the entire KWin integration is redesigned.

### `aw-watcher-input/visualization/src/index.js`

- Small browserify-era visualization entrypoint
- Experimental/manual support surface
- Not part of the maintained CI gate or main Trust-me runtime path

This file can be revisited later if the visualization becomes an actively
maintained product surface. For now it is explicitly kept as-is instead of
being carried forward accidentally.
