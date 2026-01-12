#!/bin/bash

# MTL Finder - Start All Services
# This script starts OTP, backend, and frontend in the background

set -e

echo "=========================================="
echo "MTL Finder - Starting All Services"
echo "=========================================="
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "Error: .env file not found!"
    echo "Please run ./setup.sh first."
    exit 1
fi

# Load environment variables
source ./.env

# Check if otp-data exists
if [ ! -d "otp-data" ]; then
    echo "Error: OTP data directory not found!"
    echo "Please run ./setup.sh first."
    exit 1
fi

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "Error: Docker is not running. Please start Docker first."
    exit 1
fi

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "Error: 'uv' is not installed."
    echo "Install it with: curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

echo "Step 1: Starting Photon Geocoder"
echo "================================="
echo ""

# Start Photon
docker compose -f docker-compose.photon.yml up -d

echo "✓ Photon container started"
echo "  Note: First start will download Canada data (~8GB)"
echo "  API will be available at: http://localhost:2322"
echo ""

echo "Step 2: Starting OpenTripPlanner"
echo "================================="
echo ""

# Start OTP
docker compose -f docker-compose.otp.yml up -d

echo "✓ OTP container started"
echo "  Waiting for graph to build (this may take 5-10 minutes)..."
echo ""

# Wait for OTP to be ready
echo -n "Building graph"
while true; do
    if docker logs otp-montreal 2>&1 | grep -q "Grizzly server running"; then
        echo ""
        echo "✓ OTP graph built and server ready!"
        break
    fi
    echo -n "."
    sleep 5
done

echo "  API available at: http://localhost:8080/otp/routers/default"
echo ""

echo "Step 3: Starting Backend API"
echo "============================="
echo ""

# Start backend in background
cd src/backend
uv run uvicorn main:app --host 0.0.0.0 --port ${API_PORT} > ../../backend.log 2>&1 &
BACKEND_PID=$!
echo $BACKEND_PID > ../../backend.pid
cd ../..

echo "✓ Backend started (PID: $BACKEND_PID)"
echo "  Logs: tail -f backend.log"
echo "  API: ${API_URL}"
echo ""

# Wait for backend to start
sleep 3

echo "Step 4: Starting Frontend"
echo "========================="
echo ""

# Start frontend in background
cd src/frontend
uv run streamlit run main.py --server.port ${FRONTEND_PORT} > ../../frontend.log 2>&1 &
FRONTEND_PID=$!
echo $FRONTEND_PID > ../../frontend.pid
cd ../..

echo "✓ Frontend started (PID: $FRONTEND_PID)"
echo "  Logs: tail -f frontend.log"
echo "  URL: http://localhost:${FRONTEND_PORT}"
echo ""

echo "=========================================="
echo "All Services Started!"
echo "=========================================="
echo ""
echo "Services:"
echo "  - Photon:   http://localhost:2322"
echo "  - OTP:      http://localhost:8080"
echo "  - Backend:  ${API_URL}"
echo "  - Frontend: http://localhost:${FRONTEND_PORT}"
echo ""
echo "Logs:"
echo "  - Photon:   docker logs -f photon-geocoder"
echo "  - OTP:      docker logs -f otp-montreal"
echo "  - Backend:  tail -f backend.log"
echo "  - Frontend: tail -f frontend.log"
echo ""
echo "To stop all services:"
echo "  ./stop.sh"
echo ""
