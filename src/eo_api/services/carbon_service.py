"""Carbon intensity service - queries Supabase for carbon and fuel mix data."""

from datetime import date, datetime, timedelta
from supabase import Client

from ..models import (
    CarbonIntensity,
    CarbonIntensityResponse,
    FuelMix,
    FuelMixResponse,
)


class CarbonService:
    """Service for querying carbon intensity and fuel mix data."""

    def __init__(self, db: Client):
        self.db = db

    def get_carbon_intensity_current(self) -> CarbonIntensityResponse:
        """Get most recent carbon intensity reading."""
        response = (
            self.db.table("carbon_intensity")
            .select("*")
            .order("datetime", desc=True)
            .limit(1)
            .execute()
        )

        data = [CarbonIntensity(**row) for row in response.data]
        return CarbonIntensityResponse(data=data, count=len(data))

    def get_carbon_intensity_by_date(self, target_date: date) -> CarbonIntensityResponse:
        """Get carbon intensity readings for a specific date."""
        start = datetime.combine(target_date, datetime.min.time())
        end = start + timedelta(days=1)

        response = (
            self.db.table("carbon_intensity")
            .select("*")
            .gte("datetime", start.isoformat())
            .lt("datetime", end.isoformat())
            .order("datetime")
            .execute()
        )

        data = [CarbonIntensity(**row) for row in response.data]
        return CarbonIntensityResponse(data=data, count=len(data))

    def get_carbon_intensity_range(
        self, from_date: date, to_date: date
    ) -> CarbonIntensityResponse:
        """Get carbon intensity for a date range."""
        start = datetime.combine(from_date, datetime.min.time())
        end = datetime.combine(to_date, datetime.min.time()) + timedelta(days=1)

        response = (
            self.db.table("carbon_intensity")
            .select("*")
            .gte("datetime", start.isoformat())
            .lt("datetime", end.isoformat())
            .order("datetime")
            .execute()
        )

        data = [CarbonIntensity(**row) for row in response.data]
        return CarbonIntensityResponse(data=data, count=len(data))

    # ============== Fuel Mix ==============

    def get_fuel_mix_current(self) -> FuelMixResponse:
        """Get most recent fuel mix reading."""
        response = (
            self.db.table("fuel_mix")
            .select("*")
            .order("datetime", desc=True)
            .limit(1)
            .execute()
        )

        data = [FuelMix(**row) for row in response.data]
        return FuelMixResponse(data=data, count=len(data))

    def get_fuel_mix_by_date(self, target_date: date) -> FuelMixResponse:
        """Get fuel mix readings for a specific date."""
        start = datetime.combine(target_date, datetime.min.time())
        end = start + timedelta(days=1)

        response = (
            self.db.table("fuel_mix")
            .select("*")
            .gte("datetime", start.isoformat())
            .lt("datetime", end.isoformat())
            .order("datetime")
            .execute()
        )

        data = [FuelMix(**row) for row in response.data]
        return FuelMixResponse(data=data, count=len(data))
