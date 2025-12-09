"""Price data service - queries Supabase for system and day-ahead prices."""

from datetime import date
from decimal import Decimal
from supabase import Client

from ..models import (
    SystemPrice,
    SystemPriceResponse,
    DayAheadPrice,
    DayAheadPriceResponse,
    MonthlyAverage,
)


class PriceService:
    """Service for querying price data from Supabase."""

    def __init__(self, db: Client):
        self.db = db

    def get_system_prices_latest(self, limit: int = 48) -> SystemPriceResponse:
        """Get most recent system prices."""
        response = (
            self.db.table("system_prices")
            .select("*")
            .order("settlement_date", desc=True)
            .order("settlement_period", desc=True)
            .limit(limit)
            .execute()
        )

        prices = [SystemPrice(**row) for row in response.data]
        return SystemPriceResponse(data=prices, count=len(prices))

    def get_system_prices_by_date(self, target_date: date) -> SystemPriceResponse:
        """Get system prices for a specific date."""
        response = (
            self.db.table("system_prices")
            .select("*")
            .eq("settlement_date", target_date.isoformat())
            .order("settlement_period")
            .execute()
        )

        prices = [SystemPrice(**row) for row in response.data]
        return SystemPriceResponse(data=prices, count=len(prices))

    def get_system_prices_range(
        self, from_date: date, to_date: date
    ) -> SystemPriceResponse:
        """Get system prices for a date range."""
        response = (
            self.db.table("system_prices")
            .select("*")
            .gte("settlement_date", from_date.isoformat())
            .lte("settlement_date", to_date.isoformat())
            .order("settlement_date")
            .order("settlement_period")
            .execute()
        )

        prices = [SystemPrice(**row) for row in response.data]
        return SystemPriceResponse(data=prices, count=len(prices))

    def get_system_price_monthly_avg(self, year: int, month: int) -> MonthlyAverage:
        """Calculate monthly average system price for PPA settlement."""
        # Build date range for the month
        from_date = date(year, month, 1)
        if month == 12:
            to_date = date(year + 1, 1, 1)
        else:
            to_date = date(year, month + 1, 1)

        # Query all prices for the month
        response = (
            self.db.table("system_prices")
            .select("price")
            .gte("settlement_date", from_date.isoformat())
            .lt("settlement_date", to_date.isoformat())
            .execute()
        )

        if not response.data:
            raise ValueError(f"No data found for {year}-{month:02d}")

        prices = [Decimal(str(row["price"])) for row in response.data]

        return MonthlyAverage(
            year=year,
            month=month,
            average_price=sum(prices) / len(prices),
            min_price=min(prices),
            max_price=max(prices),
            settlement_periods=len(prices),
            price_type="system",
        )

    # ============== Day-Ahead Prices ==============

    def get_dayahead_prices_latest(self, limit: int = 48) -> DayAheadPriceResponse:
        """Get most recent day-ahead prices."""
        response = (
            self.db.table("day_ahead_prices")
            .select("*")
            .order("settlement_date", desc=True)
            .order("settlement_period", desc=True)
            .limit(limit)
            .execute()
        )

        prices = [DayAheadPrice(**row) for row in response.data]
        return DayAheadPriceResponse(data=prices, count=len(prices))

    def get_dayahead_prices_by_date(self, target_date: date) -> DayAheadPriceResponse:
        """Get day-ahead prices for a specific date."""
        response = (
            self.db.table("day_ahead_prices")
            .select("*")
            .eq("settlement_date", target_date.isoformat())
            .order("settlement_period")
            .execute()
        )

        prices = [DayAheadPrice(**row) for row in response.data]
        return DayAheadPriceResponse(data=prices, count=len(prices))

    def get_dayahead_price_monthly_avg(self, year: int, month: int) -> MonthlyAverage:
        """Calculate monthly average day-ahead price."""
        from_date = date(year, month, 1)
        if month == 12:
            to_date = date(year + 1, 1, 1)
        else:
            to_date = date(year, month + 1, 1)

        response = (
            self.db.table("day_ahead_prices")
            .select("price")
            .gte("settlement_date", from_date.isoformat())
            .lt("settlement_date", to_date.isoformat())
            .execute()
        )

        if not response.data:
            raise ValueError(f"No data found for {year}-{month:02d}")

        prices = [Decimal(str(row["price"])) for row in response.data]

        return MonthlyAverage(
            year=year,
            month=month,
            average_price=sum(prices) / len(prices),
            min_price=min(prices),
            max_price=max(prices),
            settlement_periods=len(prices),
            price_type="dayahead",
        )
