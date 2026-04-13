#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

echo "========================================="
echo "Stopping all LiveGen services..."
echo "========================================="

docker-compose down

echo ""
echo "All services stopped."
echo ""
echo "Note: Volume 'livekit-data' preserved."
echo "To remove: docker volume rm livegen_livekit-data"
