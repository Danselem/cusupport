.PHONY: install lint typecheck test format run clean help

help:
	@echo "PipeGen - Customer Service Conversational AI"
	@echo ""
	@echo "Available commands:"
	@echo "  make install    - Install all dependencies including dev"
	@echo "  make lint       - Run ruff linter"
	@echo "  make typecheck  - Run mypy type checker"
	@echo "  make test       - Run pytest tests"
	@echo "  make format     - Format code with ruff"
	@echo "  make run        - Run the agent"
	@echo "  make clean      - Remove cache files"
	@echo "  make env        - Create and configure environment variables"

install:
	uv pip install -e ".[dev]"

lint:
	uv run ruff check src/

typecheck:
	uv run mypy src/

test:
	uv run pytest

format:
	uv run ruff format src/

run:
	uv run python -m pipegen.agent -t webrtc

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true

env:
	cp .env.example .env