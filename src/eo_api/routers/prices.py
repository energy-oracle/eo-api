"""Price endpoints for UK energy market data."""

from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Path, Query
from supabase import Client

from ..database import get_db
from ..models import SystemPriceResponse, DayAheadPriceResponse, MonthlyAverage
from ..services import PriceService

router = APIRouter(prefix="/uk/prices", tags=["prices"])


def get_price_service(db: Client = Depends(get_db)) -> PriceService:
    """Dependency to get price service."""
    return PriceService(db)


# ============== System Prices ==============
# Note: Order matters! Specific routes before parameterized ones.


@router.get("/system/latest", response_model=SystemPriceResponse)
def get_system_prices_latest(
    limit: int = Query(default=48, le=500, description="Number of records to return"),
    service: PriceService = Depends(get_price_service),
):
    """
    Get most recent system prices (SSP/SBP).

    Returns the latest settlement periods, ordered by date and period descending.
    Default limit is 48 (one day of half-hourly data).
    """
    return service.get_system_prices_latest(limit=limit)


@router.get("/system/range", response_model=SystemPriceResponse)
def get_system_prices_range(
    from_date: date = Query(..., description="Start date (inclusive)"),
    to_date: date = Query(..., description="End date (inclusive)"),
    service: PriceService = Depends(get_price_service),
):
    """
    Get system prices for a date range.

    Maximum range is 31 days to prevent excessive data transfer.
    """
    if (to_date - from_date).days > 31:
        raise HTTPException(
            status_code=400, detail="Date range cannot exceed 31 days"
        )

    return service.get_system_prices_range(from_date, to_date)


@router.get("/system/monthly-avg/{year}/{month}", response_model=MonthlyAverage)
def get_system_price_monthly_avg(
    year: int = Path(..., description="Year (e.g., 2025)"),
    month: int = Path(..., ge=1, le=12, description="Month (1-12)"),
    service: PriceService = Depends(get_price_service),
):
    """
    Get monthly average system price for PPA settlement.

    This is the key endpoint for PPA settlement calculations.
    Returns the arithmetic mean of all settlement period prices for the month.
    """
    try:
        return service.get_system_price_monthly_avg(year, month)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/system/date/{target_date}", response_model=SystemPriceResponse)
def get_system_prices_by_date(
    target_date: date = Path(..., description="Date in YYYY-MM-DD format"),
    service: PriceService = Depends(get_price_service),
):
    """
    Get system prices for a specific date.

    Returns all 48 settlement periods for the given date.
    """
    return service.get_system_prices_by_date(target_date)


# ============== Day-Ahead Prices ==============


@router.get("/dayahead/latest", response_model=DayAheadPriceResponse)
def get_dayahead_prices_latest(
    limit: int = Query(default=48, le=500, description="Number of records to return"),
    service: PriceService = Depends(get_price_service),
):
    """
    Get most recent day-ahead prices (APXMIDP).

    Day-ahead prices are used for forward pricing and some PPA structures.
    """
    return service.get_dayahead_prices_latest(limit=limit)


@router.get("/dayahead/monthly-avg/{year}/{month}", response_model=MonthlyAverage)
def get_dayahead_price_monthly_avg(
    year: int = Path(..., description="Year (e.g., 2025)"),
    month: int = Path(..., ge=1, le=12, description="Month (1-12)"),
    service: PriceService = Depends(get_price_service),
):
    """
    Get monthly average day-ahead price.

    Alternative to system price for some PPA structures.
    """
    try:
        return service.get_dayahead_price_monthly_avg(year, month)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/dayahead/date/{target_date}", response_model=DayAheadPriceResponse)
def get_dayahead_prices_by_date(
    target_date: date = Path(..., description="Date in YYYY-MM-DD format"),
    service: PriceService = Depends(get_price_service),
):
    """Get day-ahead prices for a specific date."""
    return service.get_dayahead_prices_by_date(target_date)
