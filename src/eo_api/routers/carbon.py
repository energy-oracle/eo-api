"""Carbon intensity and fuel mix endpoints."""

from datetime import date
from fastapi import APIRouter, Depends, Query
from supabase import Client

from ..database import get_db
from ..models import CarbonIntensityResponse, FuelMixResponse
from ..services import CarbonService

router = APIRouter(prefix="/uk/carbon", tags=["carbon"])


def get_carbon_service(db: Client = Depends(get_db)) -> CarbonService:
    """Dependency to get carbon service."""
    return CarbonService(db)


# ============== Carbon Intensity ==============


@router.get("/intensity/current", response_model=CarbonIntensityResponse)
def get_carbon_intensity_current(
    service: CarbonService = Depends(get_carbon_service),
):
    """
    Get current carbon intensity.

    Returns the most recent carbon intensity reading in gCO2/kWh.
    Useful for real-time ESG reporting and green tariff calculations.
    """
    return service.get_carbon_intensity_current()


@router.get("/intensity/{target_date}", response_model=CarbonIntensityResponse)
def get_carbon_intensity_by_date(
    target_date: date,
    service: CarbonService = Depends(get_carbon_service),
):
    """
    Get carbon intensity readings for a specific date.

    Returns all half-hourly readings for the given date.
    """
    return service.get_carbon_intensity_by_date(target_date)


@router.get("/intensity/range/", response_model=CarbonIntensityResponse)
def get_carbon_intensity_range(
    from_date: date = Query(..., description="Start date (inclusive)"),
    to_date: date = Query(..., description="End date (inclusive)"),
    service: CarbonService = Depends(get_carbon_service),
):
    """
    Get carbon intensity for a date range.

    Useful for calculating average carbon intensity over a billing period.
    """
    return service.get_carbon_intensity_range(from_date, to_date)


# ============== Fuel Mix ==============


@router.get("/fuelmix/current", response_model=FuelMixResponse)
def get_fuel_mix_current(
    service: CarbonService = Depends(get_carbon_service),
):
    """
    Get current generation fuel mix.

    Shows percentage breakdown of electricity generation by source:
    wind, solar, nuclear, gas, coal, hydro, biomass, imports, other.
    """
    return service.get_fuel_mix_current()


@router.get("/fuelmix/{target_date}", response_model=FuelMixResponse)
def get_fuel_mix_by_date(
    target_date: date,
    service: CarbonService = Depends(get_carbon_service),
):
    """Get fuel mix readings for a specific date."""
    return service.get_fuel_mix_by_date(target_date)
