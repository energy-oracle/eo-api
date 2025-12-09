"""PPA Settlement calculation endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from supabase import Client

from ..database import get_db
from ..models import SettlementRequest, SettlementResult
from ..services import SettlementService

router = APIRouter(prefix="/uk/settlement", tags=["settlement"])


def get_settlement_service(db: Client = Depends(get_db)) -> SettlementService:
    """Dependency to get settlement service."""
    return SettlementService(db)


@router.post("/calculate", response_model=SettlementResult)
def calculate_settlement(
    request: SettlementRequest,
    service: SettlementService = Depends(get_settlement_service),
):
    """
    Calculate PPA settlement for a given month.

    **Standard PPA Formula:**
    ```
    Settlement Price = Monthly Average Price - Discount
    Settlement Amount = Settlement Price × Volume (if volume provided)
    ```

    **Example Request:**
    ```json
    {
        "year": 2025,
        "month": 11,
        "discount_per_mwh": 5.00,
        "volume_mwh": 14200,
        "price_type": "system"
    }
    ```

    **Example Response:**
    ```json
    {
        "year": 2025,
        "month": 11,
        "price_type": "system",
        "average_price": 72.50,
        "discount": 5.00,
        "settlement_price": 67.50,
        "volume_mwh": 14200,
        "settlement_amount": 958500.00,
        "settlement_periods": 1440,
        "unit": "GBP/MWh",
        "currency": "GBP"
    }
    ```

    This endpoint provides audit-grade settlement calculations that both
    parties in a PPA can rely on, eliminating disputes over reference prices.
    """
    try:
        return service.calculate_settlement(request)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
