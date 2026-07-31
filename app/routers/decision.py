from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from app.schemas import DecisionRequest, DecisionResponse
from app.services.config_loader import ConfigNotFoundError, load_rating, load_rules
from app.services.rating_engine import PremiumCalculationError, calculate_premium
from app.services.rules_engine import Decision, evaluate

router = APIRouter(prefix="/api", tags=["decision"])


@router.post("/decision", response_model=DecisionResponse)
def post_decision(
    request: DecisionRequest,
    state: Optional[str] = Query(None, description="State identifier, e.g. 'california'"),
):
    if not state:
        raise HTTPException(status_code=400, detail="Query parameter 'state' is required")

    try:
        rules_config = load_rules(state)
    except ConfigNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    decision, reason = evaluate(rules_config, request.answers)

    premium = None
    if decision == Decision.APPROVE:
        try:
            rating_config = load_rating(state)
        except ConfigNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

        try:
            premium = calculate_premium(rating_config, request.answers)
        except PremiumCalculationError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

    return DecisionResponse(status=decision.value, reason=reason, premium=premium)
