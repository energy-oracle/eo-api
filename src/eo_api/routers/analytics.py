"""Analytics endpoints - advanced price and carbon analytics."""

from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query
from supabase import Client

from ..database import get_db
from ..models import (
    DailyAverageResponse,
    WeeklyAverageResponse,
    PeakOffPeakBreakdown,
    PriceStatistics,
    CarbonWeightedPrice,
    DailyCarbonSummaryResponse,
)
from ..services import AnalyticsService

router = APIRouter(prefix="/uk/analytics", tags=["analytics"])


def get_analytics_service(db: Client = Depends(get_db)) -> AnalyticsService:
    """Dependency to get analytics service."""
    return AnalyticsService(db)


# ============== Price Analytics ==============


@router.get("/prices/daily", response_model=DailyAverageResponse)
def get_daily_averages(
    from_date: date = Query(..., description="Start date"),
    to_date: date = Query(..., description="End date"),
    price_type: str = Query(default="system", description="system or dayahead"),
    service: AnalyticsService = Depends(get_analytics_service),
):
    """
    Get daily average prices for a date range.

    Useful for:
    - Daily price trend analysis
    - Comparing day-over-day volatility
    - Identifying high/low price days
    """
    if (to_date - from_date).days > 90:
        raise HTTPException(status_code=400, detail="Date range cannot exceed 90 days")

    return service.get_daily_averages(from_date, to_date, price_type)


@router.get("/prices/weekly", response_model=WeeklyAverageResponse)
def get_weekly_averages(
    from_date: date = Query(..., description="Start date"),
    to_date: date = Query(..., description="End date"),
    price_type: str = Query(default="system", description="system or dayahead"),
    service: AnalyticsService = Depends(get_analytics_service),
):
    """
    Get weekly average prices for a date range.

    Useful for:
    - Weekly trend analysis
    - Seasonal pattern identification
    - Longer-term price forecasting
    """
    if (to_date - from_date).days > 365:
        raise HTTPException(status_code=400, detail="Date range cannot exceed 365 days")

    return service.get_weekly_averages(from_date, to_date, price_type)


@router.get("/prices/peak-offpeak", response_model=PeakOffPeakBreakdown)
def get_peak_offpeak_breakdown(
    from_date: date = Query(..., description="Start date"),
    to_date: date = Query(..., description="End date"),
    price_type: str = Query(default="system", description="system or dayahead"),
    service: AnalyticsService = Depends(get_analytics_service),
):
    """
    Get peak vs off-peak price breakdown.

    **Peak hours:** 07:00-19:00 weekdays (settlement periods 15-38)
    **Off-peak:** Nights + weekends

    Useful for:
    - Understanding time-of-use pricing
    - Optimizing consumption patterns
    - Flexibility/demand response value analysis
    """
    if (to_date - from_date).days > 31:
        raise HTTPException(status_code=400, detail="Date range cannot exceed 31 days")

    return service.get_peak_offpeak_breakdown(from_date, to_date, price_type)


@router.get("/prices/statistics", response_model=PriceStatistics)
def get_price_statistics(
    from_date: date = Query(..., description="Start date"),
    to_date: date = Query(..., description="End date"),
    price_type: str = Query(default="system", description="system or dayahead"),
    service: AnalyticsService = Depends(get_analytics_service),
):
    """
    Get comprehensive price statistics.

    Includes:
    - Basic stats: average, median, min, max
    - Volatility: standard deviation, coefficient of variation
    - Distribution: percentiles (25th, 75th, 95th)
    - Counts: negative periods, price spikes

    Useful for:
    - Risk analysis
    - PPA pricing decisions
    - Market volatility assessment
    """
    try:
        return service.get_price_statistics(from_date, to_date, price_type)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ============== Carbon Analytics ==============


@router.get("/carbon/weighted-price", response_model=CarbonWeightedPrice)
def get_carbon_weighted_price(
    from_date: date = Query(..., description="Start date"),
    to_date: date = Query(..., description="End date"),
    service: AnalyticsService = Depends(get_analytics_service),
):
    """
    Get prices weighted by carbon intensity.

    Analyzes the "green premium" - the price difference during:
    - **Green periods:** Carbon intensity < 100 gCO2/kWh
    - **Brown periods:** Carbon intensity > 200 gCO2/kWh

    Useful for:
    - ESG reporting and strategy
    - Green tariff pricing
    - Renewable value analysis
    - Carbon-aware scheduling
    """
    if (to_date - from_date).days > 31:
        raise HTTPException(status_code=400, detail="Date range cannot exceed 31 days")

    return service.get_carbon_weighted_price(from_date, to_date)


@router.get("/carbon/daily-summary", response_model=DailyCarbonSummaryResponse)
def get_daily_carbon_summary(
    from_date: date = Query(..., description="Start date"),
    to_date: date = Query(..., description="End date"),
    service: AnalyticsService = Depends(get_analytics_service),
):
    """
    Get daily carbon intensity summaries.

    Includes:
    - Daily average, min, max intensity
    - Hours in each intensity band (very low to very high)
    - Dominant fuel source
    - Renewable percentage (wind + solar + hydro)

    Useful for:
    - ESG reporting
    - Carbon footprint calculations
    - Grid decarbonization tracking
    """
    if (to_date - from_date).days > 90:
        raise HTTPException(status_code=400, detail="Date range cannot exceed 90 days")

    return service.get_daily_carbon_summary(from_date, to_date)
