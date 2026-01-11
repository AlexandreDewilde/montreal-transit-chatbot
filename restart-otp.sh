#!/bin/bash

# Script to restart OpenTripPlanner after configuration changes
# This rebuilds the graph with BIXI and GTFS-RT support

echo "🔄 Restarting OpenTripPlanner with BIXI and STM real-time updates..."

# Stop existing container
echo "📦 Stopping existing OTP container..."
docker-compose -f docker-compose.otp.yml down

# Remove old graph to force rebuild
echo "🗑️  Removing old graph.obj to force rebuild..."
rm -f otp-data/graphs/montreal/graph.obj

# Start OTP with rebuild
echo "🚀 Starting OTP (this will rebuild the graph with new configuration)..."
echo "⏱️  Graph building will take 5-10 minutes..."
docker-compose -f docker-compose.otp.yml up -d

# Monitor logs
echo ""
echo "📋 Monitoring OTP logs (Ctrl+C to stop monitoring)..."
echo "   Look for messages about:"
echo "   - BIXI vehicle rental updater"
echo "   - STM GTFS-RT trip updates"
echo "   - STM GTFS-RT service alerts"
echo ""
docker-compose -f docker-compose.otp.yml logs -f
