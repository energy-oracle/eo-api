"""Pydantic response models for EnergyOracle API."""

from datetime import date, datetime
from decimal import Decimal
from pydantic import BaseModel, Field


# ============== System Prices ==============

class SystemPrice(BaseModel):
    """Single system price record (half-hourly settlement period)."""

    settlement_date: date
    settlement_period: int = Field(ge=1, le=50)
    system_sell_price: Decimal | None = None
    system_buy_price: Decimal | None = None
    price: Decimal = Field(description="Mid price (average of SSP and SBP)")
    data_source: str = "elexon_bmrs"


class SystemPriceResponse(BaseModel):
    """Response containing multiple system prices."""

    data: list[SystemPrice]
    count: int
    unit: str = "GBP/MWh"


# ============== Day-Ahead Prices ==============

class DayAheadPrice(BaseModel):
    """Single day-ahead price record."""

    settlement_date: date
    settlement_period: int = Field(ge=1, le=50)
    price: Decimal
    data_provider: str = "APXMIDP"
    data_source: str = "elexon_bmrs"


class DayAheadPriceResponse(BaseModel):
    """Response containing multiple day-ahead prices."""

    data: list[DayAheadPrice]
    count: int
    unit: str = "GBP/MWh"


# ============== Monthly Averages ==============

class MonthlyAverage(BaseModel):
    """Monthly average price for PPA settlement."""

    year: int
    month: int
    average_price: Decimal = Field(description="Arithmetic mean of all settlement periods")
    min_price: Decimal
    max_price: Decimal
    settlement_periods: int = Field(description="Number of periods in calculation")
    unit: str = "GBP/MWh"
    price_type: str = Field(description="system or dayahead")


# ============== Carbon Intensity ==============

class CarbonIntensity(BaseModel):
    """Single carbon intensity reading."""

    datetime: datetime
    intensity: int = Field(description="gCO2 per kWh")
    intensity_index: str | None = Field(
        default=None,
        description="very low, low, moderate, high, very high"
    )
    data_source: str = "national_grid"


class CarbonIntensityResponse(BaseModel):
    """Response containing carbon intensity data."""

    data: list[CarbonIntensity]
    count: int
    unit: str = "gCO2/kWh"


# ============== Fuel Mix ==============

class FuelMix(BaseModel):
    """Generation fuel mix breakdown."""

    datetime: datetime
    biomass: Decimal | None = None
    coal: Decimal | None = None
    gas: Decimal | None = None
    hydro: Decimal | None = None
    imports: Decimal | None = None
    nuclear: Decimal | None = None
    other: Decimal | None = None
    solar: Decimal | None = None
    wind: Decimal | None = None
    data_source: str = "national_grid"


class FuelMixResponse(BaseModel):
    """Response containing fuel mix data."""

    data: list[FuelMix]
    count: int
    unit: str = "percentage"


# ============== Settlement ==============

class SettlementRequest(BaseModel):
    """Request to calculate PPA settlement."""

    year: int
    month: int
    discount_per_mwh: Decimal = Field(
        default=Decimal("0"),
        description="Discount from average price (£/MWh)"
    )
    volume_mwh: Decimal | None = Field(
        default=None,
        description="Optional volume for total calculation"
    )
    price_type: str = Field(
        default="system",
        description="Price index: 'system' or 'dayahead'"
    )


class SettlementResult(BaseModel):
    """PPA settlement calculation result."""

    year: int
    month: int
    price_type: str
    average_price: Decimal = Field(description="Average market price")
    discount: Decimal
    settlement_price: Decimal = Field(description="average_price - discount")
    volume_mwh: Decimal | None = None
    settlement_amount: Decimal | None = Field(
        default=None,
        description="settlement_price × volume_mwh (if volume provided)"
    )
    settlement_periods: int
    unit: str = "GBP/MWh"
    currency: str = "GBP"


# ============== Analytics ==============

class DailyAverage(BaseModel):
    """Daily average price."""

    date: date
    average_price: Decimal
    min_price: Decimal
    max_price: Decimal
    settlement_periods: int
    unit: str = "GBP/MWh"


class DailyAverageResponse(BaseModel):
    """Response containing daily averages."""

    data: list[DailyAverage]
    count: int
    price_type: str


class WeeklyAverage(BaseModel):
    """Weekly average price."""

    week_start: date
    week_end: date
    week_number: int
    average_price: Decimal
    min_price: Decimal
    max_price: Decimal
    settlement_periods: int
    unit: str = "GBP/MWh"


class WeeklyAverageResponse(BaseModel):
    """Response containing weekly averages."""

    data: list[WeeklyAverage]
    count: int
    price_type: str


class PeakOffPeakBreakdown(BaseModel):
    """Peak vs Off-Peak price breakdown."""

    period: str = Field(description="day, week, month")
    start_date: date
    end_date: date

    # Peak: 07:00-19:00 weekdays (periods 15-38)
    peak_average: Decimal
    peak_min: Decimal
    peak_max: Decimal
    peak_periods: int

    # Off-Peak: nights + weekends
    offpeak_average: Decimal
    offpeak_min: Decimal
    offpeak_max: Decimal
    offpeak_periods: int

    # Spread
    peak_premium: Decimal = Field(description="peak_average - offpeak_average")
    peak_premium_pct: Decimal = Field(description="Premium as percentage")

    unit: str = "GBP/MWh"


class PriceStatistics(BaseModel):
    """Comprehensive price statistics for a period."""

    period: str = Field(description="day, week, month, year")
    start_date: date
    end_date: date
    price_type: str

    # Basic stats
    average: Decimal
    median: Decimal
    min: Decimal
    max: Decimal

    # Volatility
    std_dev: Decimal = Field(description="Standard deviation")
    volatility_pct: Decimal = Field(description="Coefficient of variation (std/mean)")

    # Distribution
    percentile_25: Decimal
    percentile_75: Decimal
    percentile_95: Decimal

    # Counts
    settlement_periods: int
    negative_periods: int = Field(description="Periods with price < 0")
    spike_periods: int = Field(description="Periods > 2x average")

    unit: str = "GBP/MWh"


class CarbonWeightedPrice(BaseModel):
    """Price weighted by carbon intensity for green premium analysis."""

    period: str
    start_date: date
    end_date: date

    # Standard average
    average_price: Decimal

    # Carbon-weighted: price when carbon < 100 gCO2/kWh
    green_average: Decimal = Field(description="Average during low-carbon periods")
    green_periods: int
    green_pct: Decimal = Field(description="% of time in green periods")

    # Brown average: price when carbon > 200 gCO2/kWh
    brown_average: Decimal = Field(description="Average during high-carbon periods")
    brown_periods: int
    brown_pct: Decimal

    # Green premium/discount
    green_premium: Decimal = Field(description="green_average - average_price")

    # Average carbon intensity
    avg_carbon_intensity: int

    unit_price: str = "GBP/MWh"
    unit_carbon: str = "gCO2/kWh"


class DailyCarbonSummary(BaseModel):
    """Daily carbon intensity summary."""

    date: date
    average_intensity: int
    min_intensity: int
    max_intensity: int

    # Time in each band
    very_low_hours: Decimal = Field(description="Hours < 50 gCO2/kWh")
    low_hours: Decimal = Field(description="Hours 50-100")
    moderate_hours: Decimal = Field(description="Hours 100-200")
    high_hours: Decimal = Field(description="Hours 200-300")
    very_high_hours: Decimal = Field(description="Hours > 300")

    # Dominant fuel
    dominant_fuel: str = Field(description="Fuel with highest average %")
    renewable_pct: Decimal = Field(description="wind + solar + hydro")

    unit: str = "gCO2/kWh"


class DailyCarbonSummaryResponse(BaseModel):
    """Response containing daily carbon summaries."""

    data: list[DailyCarbonSummary]
    count: int
