"""Settlement service - PPA settlement calculations."""

from decimal import Decimal
from supabase import Client

from ..models import SettlementRequest, SettlementResult
from .price_service import PriceService


class SettlementService:
    """Service for PPA settlement calculations."""

    def __init__(self, db: Client):
        self.db = db
        self.price_service = PriceService(db)

    def calculate_settlement(self, request: SettlementRequest) -> SettlementResult:
        """
        Calculate PPA settlement for a given month.

        Standard PPA formula:
            Settlement Price = Monthly Average Price - Discount
            Settlement Amount = Settlement Price × Volume

        Args:
            request: Settlement request with year, month, discount, and optional volume

        Returns:
            SettlementResult with calculated values
        """
        # Get monthly average based on price type
        if request.price_type == "system":
            avg = self.price_service.get_system_price_monthly_avg(
                request.year, request.month
            )
        elif request.price_type == "dayahead":
            avg = self.price_service.get_dayahead_price_monthly_avg(
                request.year, request.month
            )
        else:
            raise ValueError(f"Unknown price_type: {request.price_type}")

        # Calculate settlement price
        settlement_price = avg.average_price - request.discount_per_mwh

        # Calculate settlement amount if volume provided
        settlement_amount = None
        if request.volume_mwh is not None:
            settlement_amount = settlement_price * request.volume_mwh

        return SettlementResult(
            year=request.year,
            month=request.month,
            price_type=request.price_type,
            average_price=round(avg.average_price, 2),
            discount=request.discount_per_mwh,
            settlement_price=round(settlement_price, 2),
            volume_mwh=request.volume_mwh,
            settlement_amount=round(settlement_amount, 2) if settlement_amount else None,
            settlement_periods=avg.settlement_periods,
        )
