"""EnergyOracle API - UK energy market data for PPA settlement."""

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import get_settings
from .routers import prices_router, carbon_router, settlement_router, analytics_router

settings = get_settings()

app = FastAPI(
    title=settings.api_title,
    version=settings.api_version,
    description=settings.api_description,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(prices_router)
app.include_router(carbon_router)
app.include_router(settlement_router)
app.include_router(analytics_router)


@app.get("/", tags=["health"])
def root():
    """API root - health check and basic info."""
    return {
        "name": settings.api_title,
        "version": settings.api_version,
        "status": "healthy",
        "docs": "/docs",
    }


@app.get("/health", tags=["health"])
def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


def run():
    """Run the API server (called by CLI)."""
    uvicorn.run(
        "eo_api.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
    )


if __name__ == "__main__":
    run()
