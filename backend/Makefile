.PHONY: install dev sync run check

install:
	uv sync

dev:
	uv sync --dev

run-pipeline:
	uv run python run_pipeline.py $(DATE)

run-server:
	uv run python run_server.py

check:
	uv run pyright agents/

test:
	uv run pytest tests/

load-model:
	ollama pull llama3.2:3b
	ollama pull qwen2.5:1.5b
	ollama pull smollm2:1.7b

run-model:
	ollama serve
