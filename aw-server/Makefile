.PHONY: frontend-artifact build install test typecheck package clean

AW_WEBUI_DIR ?= $(abspath ../build/frontend-artifact)

build: frontend-artifact
	poetry install

frontend-artifact:
	mkdir -p aw_server/static/
	@if [ -f "$(AW_WEBUI_DIR)/index.html" ]; then \
		rm -rf aw_server/static/*; \
		cp -R "$(AW_WEBUI_DIR)"/. aw_server/static/; \
		echo "Synced frontend artifact from $(AW_WEBUI_DIR)"; \
	elif [ "$(SKIP_WEBUI)" = "true" ]; then \
		echo "Skipping frontend artifact generation; expected built assets at $(AW_WEBUI_DIR)"; \
	else \
		echo "Frontend artifact not found at $(AW_WEBUI_DIR). Run 'make -C .. prepare-frontend' or set AW_WEBUI_DIR." >&2; \
		exit 1; \
	fi

install:
	cp misc/aw-server.service /usr/lib/systemd/user/aw-server.service

test:
	@# Note that extensive integration tests are also run in the bundle repo,
	@# for both aw-server and aw-server-rust, but without code coverage.
	python -c 'import aw_server'
	python -m pytest tests/test_server.py

typecheck:
	python -m mypy aw_server tests --ignore-missing-imports

package: bump-version
	rm -rf dist
	pyinstaller aw-server.spec --clean --noconfirm

PYFILES=$(shell find . -name '*.py')

lint:
	ruff check .

lint-fix:
	poetry run pyupgrade --py38-plus --exit-zero-even-if-changed $(PYFILES)
	ruff check --fix .

format:
	black .

bump-version:
	@# make sure to pull tags in parent repo before running this
	poetry run python -m aw_server.__about__
	VERSION=$$(grep -oP '__version__ = "v\K[^"]+' aw_server/__about__.py | head -n1); echo $$VERSION; poetry version $$VERSION

clean:
	rm -rf build dist
	rm -rf aw_server/__pycache__
	rm -rf aw_server/static/*
	pip3 uninstall -y aw_server
