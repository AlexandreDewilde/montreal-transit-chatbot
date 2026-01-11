#!/bin/bash

# Script to start OpenTripPlanner server
set -e

echo "Starting OpenTripPlanner for Montreal..."

# Check if otp-data directory exists
if [ ! -d "otp-data/graphs/montreal" ]; then
    echo "Error: OTP data directory not found!"
    echo "Please run ./setup-otp.sh first to download the data."
    exit 1
fi

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "Error: Docker is not running. Please start Docker first."
    exit 1
fi

# Start OpenTripPlanner using docker-compose
echo "Starting OTP container..."
docker-compose -f docker-compose.otp.yml up -d

echo ""
echo "OpenTripPlanner is starting..."
echo "This may take 5-10 minutes for the graph to build on first run."
echo ""
echo "To check progress:"
echo "  docker logs -f otp-montreal"
echo ""
echo "Once ready, the API will be available at:"
echo "  http://localhost:8080/otp/routers/default"
echo ""
echo "To stop OTP:"
echo "  docker-compose -f docker-compose.otp.yml down"
echo ""

# Wait a few seconds and check if container is running
sleep 5

if docker ps | grep -q otp-montreal; then
    echo "✓ OTP container is running!"
    echo ""
    echo "Monitoring initial startup (Ctrl+C to exit monitoring)..."
    docker logs -f otp-montreal
else
    echo "✗ OTP container failed to start. Check logs with:"
    echo "  docker logs otp-montreal"
    exit 1
fi
