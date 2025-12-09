"""API routers for EnergyOracle."""

from .prices import router as prices_router
from .carbon import router as carbon_router
from .settlement import router as settlement_router
from .analytics import router as analytics_router

__all__ = ["prices_router", "carbon_router", "settlement_router", "analytics_router"]
