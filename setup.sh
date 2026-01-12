#!/bin/bash

# MTL Finder - Complete Installation Script
# This script sets up the entire application from scratch:
# 1. Prompts for API keys and creates .env file
# 2. Downloads GTFS and OSM data
# 3. Creates OTP configuration files
# 4. Installs Python dependencies (fresh uv environments)

set -e

echo "=========================================="
echo "MTL Finder - Fresh Installation"
echo "=========================================="
echo ""

# Check if .env already exists
if [ -f .env ]; then
    echo "Warning: .env file already exists."
    read -p "Do you want to overwrite it? (y/n): " overwrite
    if [ "$overwrite" != "y" ]; then
        echo "Using existing .env file..."
        echo ""
    else
        rm .env
    fi
fi

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "Step 1: API Keys Configuration"
    echo "================================"
    echo ""

    # Prompt for STM API key
    echo "1. STM API Key (for real-time transit data)"
    echo "   Register at: https://portail.developpeurs.stm.info/apihub"
    echo "   Create an application and get the API key (NOT client_secret)"
    read -p "   Enter STM API Key: " STM_API_KEY
    echo ""

    # Prompt for Mistral API key
    echo "2. Mistral AI API Key (for natural language understanding)"
    echo "   Get it from: https://console.mistral.ai/"
    read -p "   Enter Mistral API Key: " MISTRAL_API_KEY
    echo ""

    # Prompt for custom ports/URLs
    echo "3. Server Configuration"
    read -p "   Use default ports and URLs? (y/n) [default: y]: " use_defaults
    use_defaults=${use_defaults:-y}
    echo ""

    if [ "$use_defaults" != "y" ]; then
        read -p "   Backend port [default: 8000]: " API_PORT
        API_PORT=${API_PORT:-8000}
        read -p "   Frontend port [default: 8501]: " FRONTEND_PORT
        FRONTEND_PORT=${FRONTEND_PORT:-8501}
        API_URL="http://localhost:${API_PORT}"
    else
        API_PORT=8000
        FRONTEND_PORT=8501
        API_URL="http://localhost:8000"
    fi
    echo ""

    # Create .env file
    cat > .env <<EOF
# Backend
API_URL=${API_URL}
API_PORT=${API_PORT}

# Frontend
FRONTEND_PORT=${FRONTEND_PORT}

# Mistral AI
MISTRAL_API_KEY=${MISTRAL_API_KEY}
MISTRAL_MODEL=mistral-small-latest

# STM Real-time API
STM_API_KEY=${STM_API_KEY}

# Photon Geocoding Service
PHOTON_URL=http://localhost:2322
EOF

    echo "✓ .env file created successfully!"
    echo ""
fi

# Load environment variables (needed for OTP config)
source ./.env

echo "Step 2: OpenTripPlanner Setup"
echo "=============================="
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "Error: Docker is not running. Please start Docker first."
    exit 1
fi

# Create directories
echo "Creating OTP directory..."
mkdir -p otp-data

echo "Downloading STM GTFS data..."
curl -L "https://www.stm.info/sites/default/files/gtfs/gtfs_stm.zip" \
  -o otp-data/stm.gtfs.zip

echo "Downloading Quebec OSM data..."
curl -L "https://download.geofabrik.de/north-america/canada/quebec-latest.osm.pbf" \
  -o otp-data/quebec.osm.pbf

echo "Creating build-config.json..."
cat > otp-data/build-config.json <<'EOF'
{
  "areaVisibility": true,
  "parentStopLinking": true,
  "osmWayPropertySet": "default",
  "elevationUnitMultiplier": 1,
  "boardingLocationTags": [
    "ref",
    "name"
  ]
}
EOF

echo "Creating otp-config.json (real-time updaters for OTP 2.x)..."
cat > otp-data/otp-config.json <<EOF
{
  "otpFeatures": {
    "SandboxAPIGeocoder": false,
    "SandboxAPIMapboxVectorTilesApi": false
  },
  "updaters": [
    {
      "type": "vehicle-rental",
      "sourceType": "gbfs",
      "network": "BIXI",
      "url": "https://gbfs.velobixi.com/gbfs/gbfs.json",
      "frequency": "1m"
    },
    {
      "type": "real-time-alerts",
      "frequency": "30s",
      "url": "https://api.stm.info/pub/od/gtfs-rt/ic/v2/alerts",
      "feedId": "STM",
      "headers": {
        "apikey": "${STM_API_KEY}"
      }
    },
    {
      "type": "stop-time-updater",
      "frequency": "30s",
      "url": "https://api.stm.info/pub/od/gtfs-rt/ic/v2/tripUpdates",
      "feedId": "STM",
      "fuzzyTripMatching": true,
      "headers": {
        "apikey": "${STM_API_KEY}"
      }
    }
  ]
}
EOF

echo "Creating router-config.json..."
cat > otp-data/router-config.json <<'EOF'
{
  "routingDefaults": {
    "walkSpeed": 1.3,
    "bikeSpeed": 5.0,
    "carSpeed": 40.0,
    "numItineraries": 5,
    "transferPenalty": 0,
    "waitReluctance": 0.95,
    "walkReluctance": 2.0,
    "stairsReluctance": 1.65,
    "walkBoardCost": 60,
    "allowBikeRental": true,
    "bikeRentalPickupTime": 60,
    "bikeRentalDropoffTime": 30,
    "maxTransfers": 5,
    "searchWindow": "2h",
    "itineraryFiltering": 1.5
  },
  "timeout": 10,
  "requestLogFile": "/var/otp/requestLog.csv"
}
EOF

echo "✓ OTP configuration complete!"
echo ""

echo "Step 3: Python Dependencies"
echo "============================"
echo ""

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "Error: 'uv' is not installed."
    echo "Install it with: curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

# Clean and install backend dependencies
echo "Cleaning backend environment..."
cd src/backend
rm -rf .venv uv.lock 2>/dev/null || true
echo "Installing backend dependencies..."
uv sync
cd ../..

# Clean and install frontend dependencies
echo "Cleaning frontend environment..."
cd src/frontend
rm -rf .venv uv.lock 2>/dev/null || true
echo "Installing frontend dependencies..."
uv sync
cd ../..

echo "✓ Python dependencies installed!"
echo ""

echo "=========================================="
echo "Installation Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo ""
echo "1. Start all services:"
echo "   ./start.sh"
echo ""
echo "2. Access the application:"
echo "   Frontend: http://localhost:${FRONTEND_PORT}"
echo "   Backend:  ${API_URL}"
echo "   OTP:      http://localhost:8080"
echo "   Photon:   http://localhost:2322"
echo ""
echo "3. To stop all services:"
echo "   ./stop.sh"
echo ""
echo "Notes:"
echo "  - OTP may take 5-10 minutes to build the graph on first startup"
echo "  - Photon will download Canada geocoding data (~8GB) on first start"
echo ""
