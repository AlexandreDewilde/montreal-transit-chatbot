#!/bin/bash

# Script to setup OpenTripPlanner for Montreal
# This script downloads GTFS data for STM and OSM data for Montreal

set -e

echo "Setting up OpenTripPlanner for Montreal..."

# Create directories
mkdir -p otp-data/graphs/montreal

echo "Downloading STM GTFS data..."
# STM (Société de transport de Montréal) GTFS feed
curl -L "https://www.stm.info/sites/default/files/gtfs/gtfs_stm.zip" \
  -o otp-data/graphs/montreal/stm.gtfs.zip

echo "Downloading Montreal OSM data..."
# Download Montreal region OSM data from Geofabrik
curl -L "https://download.geofabrik.de/north-america/canada/quebec-latest.osm.pbf" \
  -o otp-data/graphs/montreal/quebec.osm.pbf

echo "Creating build-config.json..."

# Load API key from .env
source .env 2>/dev/null || true

cat > otp-data/graphs/montreal/build-config.json <<EOF
{
  "areaVisibility": true,
  "parentStopLinking": true,
  "osmWayPropertySet": "default",
  "elevationUnitMultiplier": 1,
  "boardingLocationTags": [
    "ref",
    "name"
  ],
  "updaters": [
    {
      "type": "vehicle-rental",
      "sourceType": "gbfs",
      "network": "BIXI",
      "url": "https://gbfs.velobixi.com/gbfs/gbfs.json",
      "frequencySec": 60
    },
    {
      "type": "stop-time-updater",
      "frequencySec": 30,
      "sourceType": "gtfs-http",
      "url": "https://api.stm.info/pub/od/gtfs-rt/ic/v2/tripUpdates",
      "feedId": "STM",
      "headers": {
        "apikey": "${STM_API_KEY}"
      }
    }
  ]
}
EOF

echo "Creating router-config.json..."
cat > otp-data/graphs/montreal/router-config.json <<'EOF'
{
  "routingDefaults": {
    "walkSpeed": 1.3,
    "bikeSpeed": 5.0,
    "carSpeed": 40.0,
    "numItineraries": 3,
    "transferPenalty": 0,
    "waitReluctance": 0.95,
    "walkReluctance": 2.0,
    "stairsReluctance": 1.65,
    "walkBoardCost": 60,
    "allowBikeRental": true,
    "bikeRentalPickupTime": 60,
    "bikeRentalDropoffTime": 30
  },
  "timeout": 5,
  "requestLogFile": "/var/otp/requestLog.csv"
}
EOF

echo ""
echo "Setup complete!"
echo ""
echo "Next steps:"
echo "1. Start OpenTripPlanner with: docker-compose -f docker-compose.otp.yml up -d"
echo "2. Wait for the graph to build (this may take 5-10 minutes)"
echo "3. Check logs with: docker logs -f otp-montreal"
echo "4. Once ready, OTP API will be available at http://localhost:8080"
echo ""
echo "To check if OTP is ready:"
echo "  curl http://localhost:8080/otp/routers/default"
echo ""
