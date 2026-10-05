"""
backend/main.py

FastAPI application for the Adaptive Carbon-Aware Workload Scheduling prototype.

Run locally with:
    uvicorn backend.main:app --reload --port 8000
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.carbon import router as carbon_router
from backend.api.scheduling import router as scheduling_router
from backend.api.workload import router as workload_router

# ---------------------------------------------------------------------------
# Application
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Adaptive Carbon-Aware Workload Scheduling",
    description=(
        "Faculty demo prototype: GRU-based CPU forecasting + "
        "carbon-intensity-aware scheduling decisions."
    ),
    version="0.1.0",
)

# ---------------------------------------------------------------------------
# CORS — allow local development origins
# ---------------------------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=[   # Vite dev server
        "http://localhost:3000",
        "http://localhost:5173",
        "https://adaptive-carbon-aware-workload-scheduling-p5h63ivxt-rudra-6a5f.vercel.app/",
        "https://adaptive-carbon-aware-workload-sche.vercel.app",
"https://vercel.com",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------

app.include_router(workload_router)
app.include_router(carbon_router)
app.include_router(scheduling_router)

# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------

@app.get("/api/health", tags=["health"])
def health() -> dict:
    """Simple liveness probe."""
    return {"status": "ok"}
