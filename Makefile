COVERAGE = --cov=src --cov-report=term-missing

.PHONY: all
all: test

.PHONY: test
test:
	uv run pytest

.PHONY: cov
cov:
	uv run pytest $(COVERAGE)

.PHONY: lint
lint:
	uv tool run ruff check src
	uv tool run mypy src

.PHONY: install
install:
	uv run sync

.PHONY: run
run:
	uv run python -m src.snipster.main

.PHONY: guirun
guirun:
	uv run flask --app src/snipster/gui/wsgi.py run --debug

.PHONY: apirun
apirun:
	uv run fastapi dev src/snipster/api.py
