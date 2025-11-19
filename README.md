# GCP/GKE Monitoring Dashboard

A comprehensive monitoring dashboard for GCP and GKE resources during high-traffic events. Built with Next.js frontend and FastAPI backend.

## Features

### 1. URL Maps Monitoring (Synthetic Testing)
- Tests all URL maps by performing HTTP requests to configured hostnames
- Reports HTTP status codes with color-coded indicators:
  - 🟢 Green: HTTP 200
  - 🟡 Yellow: HTTP 201-499
  - 🔴 Red: HTTP 500+

### 2. GKE Pods Monitoring
- Lists all non-running pods across all clusters
- Shows pod status and namespace information
- Color-coded by severity

### 3. Pub/Sub Monitoring
- Tracks unacked messages older than 5 minutes
- Shows message age and count
- Helps identify processing bottlenecks

### 4. GKE Node Pool Capacity
- Monitors node pool utilization against autoscaling limits
- Alerts when capacity reaches 80% or higher
- Accounts for regional vs zonal clusters

### 5. Pod Restart Monitoring
- Identifies pods with more than 5 restarts
- Helps catch crash loops and stability issues

### 6. Load Balancer Latency
- Monitors P95 backend latencies
- Alerts when latency exceeds 3 seconds

### 7. Spanner Metrics
- CPU utilization (high priority) - alerts > 45%
- Storage utilization - alerts > 75%

## Prerequisites

- Python 3.9+
- Node.js 18+
- GCP account with appropriate permissions
- `gcloud` CLI installed and configured

## Quick Start (macOS)

For a fully automated setup on macOS, follow these simple steps:

```bash
git clone <repository-url> gcp-gke-monitor
cd gcp-gke-monitor
cp config.example.json config.json
chmod +x setup_quickstart.sh
./setup_quickstart.sh
```

The script will:
- Install required dependencies (Homebrew, Node.js, Python, gcloud CLI)
- Authenticate with Google Cloud (opens browser)
- Set up backend and frontend dependencies
- Start both services
- Open your browser to http://localhost:3000

**Note:** Edit `config.json` with your GCP project IDs before running the script.

---

## Manual Setup

### 1. Clone the repository

```bash
cd gcp-gke-monitor
```

### 2. Configure GCP Authentication

```bash
gcloud auth login
gcloud auth application-default login
```

### 3. Create configuration file

Copy the example config and customize it with your GCP projects:

```bash
cp config.example.json config.json
```

Edit `config.json` with your project details:

```json
{
  "projects": [
    {
      "project_id": "your-project-id",
      "gke_clusters": [],
      "monitor_url_maps": true,
      "monitor_gke_pods": true,
      "monitor_pubsub": true,
      "monitor_gke_nodes": true,
      "monitor_pod_restarts": true,
      "monitor_latency": true,
      "monitor_spanner": true
    }
  ]
}
```

**Note:** The `gke_clusters` array can be left empty `[]` and the application will automatically discover all GKE clusters in the project. Alternatively, you can manually specify clusters if you want to monitor only specific ones:

```json
"gke_clusters": [
  {
    "name": "your-cluster-name",
    "location": "us-central1",
    "type": "regional"
  }
]
```

### 4. Install Backend Dependencies

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 5. Install Frontend Dependencies

```bash
cd ../frontend
npm install
```

### 6. Configure Frontend Environment (Optional)

Create a `.env.local` file in the frontend directory to customize settings:

```bash
cd frontend
cp .env.local.example .env.local
```

Edit `.env.local` to configure:
- `NEXT_PUBLIC_API_URL`: Backend API URL (default: http://localhost:8000)
- `NEXT_PUBLIC_REFRESH_INTERVAL`: Auto-refresh interval in seconds (default: 900)

Example:
```
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_REFRESH_INTERVAL=900
```

## Running the Application

### Option 1: Start Both Services Separately

**Terminal 1 - Backend:**
```bash
cd backend
source venv/bin/activate  # On Windows: venv\Scripts\activate
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

### Option 2: Use the Startup Script

```bash
npm run dev
```

This will automatically:
1. Start the backend on port 8000
2. Start the frontend on port 3000
3. Open http://localhost:3000 in your default browser

## Usage

1. Open http://localhost:3000 in your browser
2. Toggle "Pull Metrics" to ON to start monitoring
3. The dashboard will refresh automatically based on your configured interval (default: 900 seconds / 15 minutes)
4. Toggle to OFF to stop pulling metrics and reduce server load

## Configuration Options

### Backend Configuration (`config.json`)

Each project in `config.json` can be configured with these options:

- `project_id`: GCP project ID (required)
- `gke_clusters`: Array of GKE cluster configurations (optional - leave empty for auto-discovery)
  - If empty `[]`: All GKE clusters in the project will be automatically discovered
  - If specified: Only the listed clusters will be monitored
    - `name`: Cluster name
    - `location`: Region or zone
    - `type`: "regional" or "zonal"
- `monitor_url_maps`: Enable/disable URL map monitoring (default: true)
- `monitor_gke_pods`: Enable/disable pod monitoring (default: true)
- `monitor_pubsub`: Enable/disable Pub/Sub monitoring (default: true)
- `monitor_gke_nodes`: Enable/disable node pool monitoring (default: true)
- `monitor_pod_restarts`: Enable/disable restart monitoring (default: true)
- `monitor_latency`: Enable/disable latency monitoring (default: true)
- `monitor_spanner`: Enable/disable Spanner monitoring (default: true)

### Frontend Configuration (`.env.local`)

- `NEXT_PUBLIC_API_URL`: Backend API URL (default: http://localhost:8000)
- `NEXT_PUBLIC_REFRESH_INTERVAL`: Auto-refresh interval in seconds (default: 900)

## API Endpoints

- `GET /api/metrics` - Fetch all monitoring metrics
- `GET /api/health` - Health check endpoint
- `GET /` - API information

## Troubleshooting

### Authentication Issues

If you encounter authentication errors:

```bash
gcloud auth application-default login
gcloud config set project YOUR_PROJECT_ID
```

### Permission Issues

Ensure your GCP account has the following roles:
- Compute Viewer
- Kubernetes Engine Viewer
- Monitoring Viewer
- Pub/Sub Viewer
- Spanner Viewer

### Port Conflicts

If ports 3000 or 8000 are in use:

- Backend: Edit the uvicorn command to use a different port
- Frontend: Create a `.env.local` file and set `NEXT_PUBLIC_API_URL`

## Architecture

```
┌─────────────────┐         ┌──────────────────┐
│                 │         │                  │
│  Next.js        │  HTTP   │  FastAPI         │
│  Frontend       │◄───────►│  Backend         │
│  (Port 3000)    │         │  (Port 8000)     │
│                 │         │                  │
└─────────────────┘         └────────┬─────────┘
                                     │
                                     │ GCP APIs
                                     │
                            ┌────────▼─────────┐
                            │                  │
                            │  Google Cloud    │
                            │  Platform        │
                            │                  │
                            └──────────────────┘
```

## Development

### Backend Development

The backend is built with FastAPI and uses:
- Google Cloud client libraries for GCP services
- Kubernetes client for GKE operations
- Async operations for concurrent metric collection

### Frontend Development

The frontend is built with Next.js 14 and uses:
- React hooks for state management
- Axios for API calls
- TypeScript for type safety
- Automatic refresh with configurable intervals

## License

See LICENSE file for details.

## Support

For issues and questions, please create an issue in the repository.
