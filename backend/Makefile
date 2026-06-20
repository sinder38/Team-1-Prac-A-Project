.PHONY: install dev sync run check

install:
	uv sync

dev:
	uv sync --dev

run:
	uv run python run_pipeline.py $(DATE)

check:
	uv run pyright agents/

test:
	uv run pytest tests/
