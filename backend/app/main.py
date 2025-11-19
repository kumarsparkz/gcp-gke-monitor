from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import monitoring

app = FastAPI(
    title="GCP/GKE Monitoring Dashboard API",
    description="Backend API for monitoring GCP and GKE resources during Black Friday",
    version="1.0.0"
)

# Configure CORS for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(monitoring.router, prefix="/api", tags=["monitoring"])


@app.get("/")
async def root():
    return {
        "message": "GCP/GKE Monitoring Dashboard API",
        "version": "1.0.0",
        "endpoints": {
            "metrics": "/api/metrics",
            "health": "/api/health"
        }
    }
