from typing import Any, Optional

from pydantic import BaseModel


class DecisionRequest(BaseModel):
    answers: dict[str, Any]


class DecisionResponse(BaseModel):
    status: str
    reason: Optional[str] = None
    premium: Optional[float] = None
