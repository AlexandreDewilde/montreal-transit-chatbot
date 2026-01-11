# Running the MTL Finder Application

This guide provides instructions on how to run the MTL Finder application, including starting the backend, frontend, and OpenTripPlanner (OTP) services, along with configuration details and OTP management.

## Starting the Application

Ensure you have completed the [installation steps](INSTALL.md) and that Docker is running.

### Option 1: Using the `start.sh` Script (Recommended)

The `start.sh` script will start all services concurrently: OpenTripPlanner (OTP), the FastAPI backend, and the Streamlit frontend. OTP may take 5-10 minutes to build the graph on its first startup.

```bash
chmod +x start.sh
./start.sh
```

### Option 2: Manual Startup

You can start each service individually in separate terminal windows.

**1. Start OpenTripPlanner (OTP):**
OTP may take 5-10 minutes to build the graph on its first startup.
```bash
docker-compose -f docker-compose.otp.yml up -d
```
You can monitor its status with `docker logs -f otp-montreal`.

**2. Start the Backend (FastAPI):**
```bash
cd src/backend
uv run uvicorn main:app --reload --port ${API_PORT:-8000}
```
*Note: Replace `${API_PORT:-8000}` with the actual port if you customized it in your `.env` file.*

**3. Start the Frontend (Streamlit) in a new terminal:**
```bash
cd src/frontend
uv run streamlit run main.py --server.port ${FRONTEND_PORT:-8501}
```
*Note: Replace `${FRONTEND_PORT:-8501}` with the actual port if you customized it in your `.env` file.*

## Accessing the Application

- **Frontend**: `http://localhost:${FRONTEND_PORT:-8501}` (default: `http://localhost:8501`)
- **Backend API Docs**: `http://localhost:${API_PORT:-8000}/docs` (default: `http://localhost:8000/docs`)
- **OpenTripPlanner API**: `http://localhost:8080/otp`

## Configuration

The application's behavior is controlled by environment variables defined in the `.env` file at the project root. You can customize these values based on your setup.

```
# Backend
API_URL=http://localhost:8000         # URL where the backend is accessible
API_PORT=8000                         # Port for the FastAPI backend

# Frontend
FRONTEND_PORT=8501                    # Port for the Streamlit frontend

# Mistral AI
MISTRAL_API_KEY=your_mistral_key_here # Your API key for Mistral AI
MISTRAL_MODEL=mistral-small-latest    # The Mistral AI model to use

# STM Real-time API
STM_API_KEY=your_stm_key_here         # Your API key for STM Real-time data
```

## OpenTripPlanner Management

These commands are useful for managing the OTP Docker container.

### Check OTP Status
Verify if the OTP server is running and responsive.
```bash
curl http://localhost:8080/otp/routers/default
```

### View OTP Logs
To view the logs of the running OTP container.
```bash
docker logs -f otp-montreal
```

### Stop OTP
To stop the OTP service.
```bash
chmod +x stop.sh
./stop.sh
```
*(Alternatively, you can use `docker-compose -f docker-compose.otp.yml down`)*

### Restart OTP
To restart the OTP service, for example, after configuration changes.
```bash
chmod +x restart.sh
./restart.sh
```
*(Alternatively, you can use `docker-compose -f docker-compose.otp.yml restart`)*

### Rebuild OTP Graph
If you update the GTFS or OSM data in `otp-data/graphs/montreal/`, you need to rebuild the OTP graph.
```bash
# First, stop OTP
chmod +x stop.sh
./stop.sh
# Then, start OTP again to trigger a rebuild
chmod +x start-otp.sh
./start.sh
```
*(Alternatively: `docker-compose -f docker-compose.otp.yml down` followed by `docker-compose -f docker-compose.otp.yml up -d`)*
