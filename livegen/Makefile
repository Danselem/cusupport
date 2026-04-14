.PHONY: help init bootstrap install env server download run-console test test-unit lint lint-fix format frontend agent docker-build docker-up docker-down docker-logs

# Default target
help: ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

init:
	@echo "Initialising environment"
	@test -f pyproject.toml || uv init
	@rm -f hello.py
	@test -d .venv || uv venv .venv --python 3.12

bootstrap:
	@echo "Bootstrapping environment"
	uv add --requirements requirements.txt
	uv add --group dev --requirements requirements-dev.txt


install:
	@echo "Installing dependencies"
	uv sync

env:
	@echo "Creating environment variables file"
	cp .env.example .env

server:
	@echo "Starting livekit server"
	livekit-server --dev &

download:
	@echo "Downloading files"
	uv run python -m src.agent download-files

run-console:
	@echo "Running console"
	uv run python -m src.agent console

test:
	@echo "Running tests"
	uv run pytest

test-unit:
	@echo "Running unit tests only"
	uv run pytest tests/ -v

lint: ## Run code quality checks
	@echo "Running ruff checks..."
	uv run ruff check

lint-fix: ## Fix auto-fixable lint issues
	@echo "Fixing lint issues..."
	uv run ruff check --fix

format: ## Format code
	@echo "Formatting code..."
	uv run ruff format

frontend:
	cd webembed && npm run dev

agent:
	@echo "Starting u-turn..."
	uv run -m src.agent dev &

agent-console: ## Run agent in console mode (for testing voice input)
	@echo "Starting agent in console mode..."
	@echo "This runs the agent locally without Docker for voice testing"
	uv run python -m src.agent console

agent-console-docker: ## Run agent in console mode inside Docker
	@echo "Running agent console in Docker..."
	docker exec -it livegen-agent-1 /app/.venv/bin/python -m src.agent console

# Docker commands (using docker-compose)
docker-build: ## Build Docker images
	docker-compose build

docker-up: ## Start all services with Docker Compose
	docker-compose up -d
	@echo "Services started:"
	@echo "  LiveKit:   http://localhost:7880"
	@echo "  Agent:     http://localhost:50931"
	@echo "  Frontend:  http://localhost:3000 (run 'make docker-up-frontend' first)"

docker-up-frontend: ## Start frontend service
	docker-compose --profile frontend up -d frontend

docker-down: ## Stop all Docker services
	docker-compose down

docker-logs: ## View Docker logs
	docker-compose logs -f

docker-logs-agent: ## View agent logs
	docker-compose logs -f agent

docker-logs-livekit: ## View LiveKit logs
	docker-compose logs -f livekit

docker-clean: ## Remove all containers and volumes
	docker-compose down -v

# Docker commands (using plain docker run)
docker-net-create: ## Create Docker network
	@bash scripts/01-create-network.sh

docker-livekit-start: ## Start LiveKit server
	@bash scripts/02-start-livekit.sh

docker-agent-build: ## Build agent Docker image
	@bash scripts/03-build-agent.sh

docker-agent-start: ## Start agent service
	@bash scripts/04-start-agent.sh

docker-frontend-start: ## Start frontend service
	@bash scripts/05-start-frontend.sh

docker-start: ## Start all services with plain docker (LiveKit + Agent)
	@bash scripts/start-all.sh

docker-status: ## Check service status
	@bash scripts/status.sh

docker-stop: ## Stop all services
	@bash scripts/stop-all.sh

test-connection: ## Test LiveKit server connection (local)
	uv run python test_connection.py

test-connection-docker: ## Test LiveKit server from inside Docker container
	@echo "Running in agent container..."
	docker exec livegen-agent-1 /app/.venv/bin/python test_connection.py 2>&1 | grep -v "Warning\|site-packages"

test-webrtc: ## Test WebRTC with lk CLI
	@echo "Testing WebRTC with lk CLI..."
	@if ! command -v lk &> /dev/null; then \
		echo "lk CLI not found. Install with:"; \
		echo "  brew install livekit-cli"; \
		echo ""; \
		echo "Or download from: https://github.com/livekit/livekit-cli"; \
	fi
	@lk room list 2>/dev/null || echo "Could not connect - check if LiveKit is running on port 7880"

# LiveKit Server CLI commands (run inside Docker)
livekit-generate-keys: ## Generate API keys using LiveKit server container
	docker run --rm livekit/livekit-server:latest generate-keys

livekit-list-nodes: ## List LiveKit nodes
	docker run --rm --network livegen_livegen-network --env-file .env livekit/livekit-server:latest list-nodes --keys "dev:secret" --url http://livekit:7880

livekit-ports: ## Show LiveKit ports
	docker run --rm livekit/livekit-server:latest ports