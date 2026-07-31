from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from app.services.config_loader import ConfigNotFoundError, load_questions

router = APIRouter(prefix="/api", tags=["questions"])


@router.get("/questions")
def get_questions(state: Optional[str] = Query(None, description="State identifier, e.g. 'california'")):
    if not state:
        raise HTTPException(status_code=400, detail="Query parameter 'state' is required")

    try:
        return load_questions(state)
    except ConfigNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
