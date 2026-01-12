#!/bin/bash

# MTL Finder - Stop All Services
# This script stops OTP, backend, and frontend

set -e

echo "=========================================="
echo "MTL Finder - Stopping All Services"
echo "=========================================="
echo ""

# Stop backend
if [ -f backend.pid ]; then
    BACKEND_PID=$(cat backend.pid)
    if ps -p $BACKEND_PID > /dev/null 2>&1; then
        echo "Stopping backend (PID: $BACKEND_PID)..."
        kill $BACKEND_PID
        rm backend.pid
        echo "✓ Backend stopped"
    else
        echo "Backend not running (stale PID file)"
        rm backend.pid
    fi
else
    echo "Backend not running"
fi
echo ""

# Stop frontend
if [ -f frontend.pid ]; then
    FRONTEND_PID=$(cat frontend.pid)
    if ps -p $FRONTEND_PID > /dev/null 2>&1; then
        echo "Stopping frontend (PID: $FRONTEND_PID)..."
        kill $FRONTEND_PID
        rm frontend.pid
        echo "✓ Frontend stopped"
    else
        echo "Frontend not running (stale PID file)"
        rm frontend.pid
    fi
else
    echo "Frontend not running"
fi
echo ""

# Stop OTP
if docker ps | grep -q otp-montreal; then
    echo "Stopping OpenTripPlanner..."
    docker compose -f docker-compose.otp.yml down
    echo "✓ OTP stopped"
else
    echo "OTP not running"
fi
echo ""

# Stop Photon
if docker ps | grep -q photon-geocoder; then
    echo "Stopping Photon Geocoder..."
    docker compose -f docker-compose.photon.yml down
    echo "✓ Photon stopped"
else
    echo "Photon not running"
fi
echo ""

echo "=========================================="
echo "All Services Stopped"
echo "=========================================="
echo ""
