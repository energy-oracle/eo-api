"""Response models for EnergyOracle API."""

from .responses import (
    # Price models
    SystemPrice,
    SystemPriceResponse,
    DayAheadPrice,
    DayAheadPriceResponse,
    MonthlyAverage,
    # Carbon models
    CarbonIntensity,
    CarbonIntensityResponse,
    FuelMix,
    FuelMixResponse,
    # Settlement models
    SettlementRequest,
    SettlementResult,
    # Analytics models
    DailyAverage,
    DailyAverageResponse,
    WeeklyAverage,
    WeeklyAverageResponse,
    PeakOffPeakBreakdown,
    PriceStatistics,
    CarbonWeightedPrice,
    DailyCarbonSummary,
    DailyCarbonSummaryResponse,
    # Renewable/Green analytics
    RenewableGenerationIndex,
    GreenPremium,
)

__all__ = [
    # Price
    "SystemPrice",
    "SystemPriceResponse",
    "DayAheadPrice",
    "DayAheadPriceResponse",
    "MonthlyAverage",
    # Carbon
    "CarbonIntensity",
    "CarbonIntensityResponse",
    "FuelMix",
    "FuelMixResponse",
    # Settlement
    "SettlementRequest",
    "SettlementResult",
    # Analytics
    "DailyAverage",
    "DailyAverageResponse",
    "WeeklyAverage",
    "WeeklyAverageResponse",
    "PeakOffPeakBreakdown",
    "PriceStatistics",
    "CarbonWeightedPrice",
    "DailyCarbonSummary",
    "DailyCarbonSummaryResponse",
    # Renewable/Green analytics
    "RenewableGenerationIndex",
    "GreenPremium",
]
