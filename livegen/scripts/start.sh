#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

echo "========================================="
echo "Starting all LiveGen services..."
echo "========================================="

# Stop any running containers
echo "Stopping existing containers..."
docker-compose down 2>/dev/null || true

# Build and start all services (including frontend)
echo ""
echo "Building and starting all services..."
docker-compose up -d --build

# Wait for services to be healthy
echo ""
echo "Waiting for services to be healthy..."

# Check LiveKit
for i in {1..30}; do
    if curl -sf http://localhost:7880/health >/dev/null 2>&1; then
        echo "✓ LiveKit is healthy"
        break
    fi
    sleep 1
done

# Check Agent
for i in {1..30}; do
    if curl -sf http://localhost:50931/metrics/stats >/dev/null 2>&1; then
        echo "✓ Agent is healthy"
        break
    fi
    sleep 1
done

# Check Frontend
for i in {1..30}; do
    if curl -sf http://localhost:3000 >/dev/null 2>&1; then
        echo "✓ Frontend is healthy"
        break
    fi
    sleep 1
done

echo ""
echo "========================================="
echo "All services started!"
echo "========================================="
echo ""
docker-compose ps
echo ""
echo "Access points:"
echo "  - Frontend: http://localhost:3000"
echo "  - LiveKit: ws://localhost:7880"
echo "  - Agent: http://localhost:50931"
echo "  - Metrics Dashboard: http://localhost:50931/metrics/dashboard"
echo ""
echo "To view logs: docker-compose logs -f"
echo "To stop: bash scripts/stop.sh"
