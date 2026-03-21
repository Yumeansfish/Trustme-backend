.PHONY: build dev frontend-artifact prebuild precommit format check package node_modules

AW_WEBUI_DIR ?= $(abspath ../build/frontend-artifact)
ICON_SOURCE ?= ../aw-qt/media/logo/logo.png

ifeq ($(shell uname -m), arm64)
	ARCH := _arm64
else
	ARCH :=
endif
OS := $(shell uname -s)

build: prebuild
	AW_WEBUI_DIR="$(AW_WEBUI_DIR)" npm run tauri build

dev: prebuild
	AW_WEBUI_DIR="$(AW_WEBUI_DIR)" npm run tauri dev

src-tauri/icons/icon.png:
	mkdir -p src-tauri/icons
	npm run tauri icon "$(ICON_SOURCE)"

frontend-artifact:
	@mkdir -p "$(AW_WEBUI_DIR)"
	@if [ -f "$(AW_WEBUI_DIR)/index.html" ]; then \
		echo "Using frontend artifact from $(AW_WEBUI_DIR)"; \
	elif [ "$(SKIP_WEBUI)" = "true" ]; then \
		echo "Skipping frontend artifact generation; expected built assets at $(AW_WEBUI_DIR)"; \
	else \
		echo "Frontend artifact not found at $(AW_WEBUI_DIR). Run 'make -C .. prepare-frontend' or set AW_WEBUI_DIR." >&2; \
		exit 1; \
	fi

prebuild: frontend-artifact node_modules src-tauri/icons/icon.png

precommit: format check

format:
	cd src-tauri && cargo fmt

check:
	cd src-tauri && AW_WEBUI_DIR="$(AW_WEBUI_DIR)" cargo check && AW_WEBUI_DIR="$(AW_WEBUI_DIR)" cargo clippy

package:
ifeq ($(OS),Linux)
	rm -rf target/package/aw-tauri
	mkdir -p target/package/aw-tauri
	cp src-tauri/target/release/bundle/deb/*.deb target/package/aw-tauri/aw-tauri$(ARCH).deb
	cp src-tauri/target/release/bundle/rpm/*.rpm target/package/aw-tauri/aw-tauri$(ARCH).rpm
	cp src-tauri/target/release/bundle/appimage/*.AppImage target/package/aw-tauri/aw-tauri$(ARCH).AppImage

	mkdir -p dist/aw-tauri
	rm -rf dist/aw-tauri/*
	cp target/package/aw-tauri/* dist/aw-tauri/
else
	rm -rf target/package
	mkdir -p target/package
	cp src-tauri/target/release/aw-tauri target/package/aw-tauri

	mkdir -p dist
	find dist/ -maxdepth 1 -type f -delete 2>/dev/null || true
	cp target/package/* dist/
endif

node_modules: package-lock.json
	npm ci
