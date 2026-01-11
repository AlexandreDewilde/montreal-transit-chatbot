# Quick Start Guide - MTL Finder Chat

## First Time Setup (5 minutes)

### 1. Install Prerequisites
```bash
# Install UV (package manager)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Make sure Docker is installed and running
docker --version
```

### 2. Configure Environment
```bash
# Copy environment file
cp .env.example .env

# Edit .env and add your Mistral API key
# Get your key from: https://console.mistral.ai/
nano .env  # or use your favorite editor
```

### 3. Setup OpenTripPlanner
```bash
# Download Montreal transit and map data (~1.2 GB)
./setup-otp.sh

# Start OTP (takes 5-10 minutes first time)
./start-otp.sh
```

Wait until you see "Graph built successfully" in the logs.
Press Ctrl+C to exit the log view (OTP keeps running).

### 4. Install Dependencies
```bash
# Backend
cd src/backend
uv sync
cd ../..

# Frontend
cd src/frontend
uv sync
cd ../..
```

### 5. Run the Application
```bash
./run.sh
```

Visit http://localhost:8501 in your browser!

---

## Daily Usage

### Start Everything
```bash
# 1. Make sure OTP is running
docker ps | grep otp-montreal

# If not running:
./start-otp.sh

# 2. Start the app
./run.sh
```

### Stop Everything
```bash
# Stop the app (Ctrl+C in the terminal running run.sh)

# Stop OTP
docker-compose -f docker-compose.otp.yml down
```

---

## Example Questions to Ask the Chatbot

### Trip Planning
- "How do I get from McGill to Old Montreal?"
- "What's the fastest way to Parc Jean-Drapeau from downtown?"
- "Plan a bike route from Mile End to Griffintown"
- "I need to be at Place-des-Arts by 2pm, how should I leave from Atwater metro?"

### Weather
- "What's the weather like?"
- "Should I bring an umbrella today?"

### Combined
- "What's the weather and how do I get to Mont-Royal metro?"

---

## Troubleshooting

### "Cannot connect to OpenTripPlanner"
```bash
# Check if OTP is running
docker ps | grep otp-montreal

# If not, start it
./start-otp.sh

# Check logs for errors
docker logs otp-montreal
```

### "Mistral API is not configured"
```bash
# Make sure MISTRAL_API_KEY is set in .env
cat .env | grep MISTRAL_API_KEY

# Edit .env and add your key
nano .env
```

### Backend won't start
```bash
# Reinstall dependencies
cd src/backend
uv sync
cd ../..
```

---

## Useful Commands

```bash
# Check OTP status
curl http://localhost:8080/otp/routers/default

# View OTP logs
docker logs -f otp-montreal

# View running containers
docker ps

# Restart OTP
docker-compose -f docker-compose.otp.yml restart

# Backend API docs
# Open http://localhost:8000/docs
```

---

## Need Help?

- Check the full [README.md](README.md) for detailed documentation
- View API documentation at http://localhost:8000/docs (when backend is running)
- Check Docker logs: `docker logs otp-montreal`
