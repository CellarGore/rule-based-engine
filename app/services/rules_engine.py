from enum import Enum
from typing import Any, Optional

from app.services.conditions import evaluate_condition


class Decision(str, Enum):
    APPROVE = "approve"
    REFER = "refer"
    DECLINE = "decline"


_SEVERITY = {Decision.APPROVE: 0, Decision.REFER: 1, Decision.DECLINE: 2}


def evaluate(rules_config: dict, answers: dict[str, Any]) -> tuple[Decision, Optional[str]]:
    """Evaluate every rule and return the most severe matching decision.

    decline > refer > approve. Ties keep the reason of the first rule that
    reached that severity level.
    """
    best_decision = Decision.APPROVE
    best_reason: Optional[str] = None

    for rule in rules_config.get("rules", []):
        if not evaluate_condition(rule["when"], answers):
            continue

        decision = Decision(rule["decision"])
        if _SEVERITY[decision] > _SEVERITY[best_decision]:
            best_decision = decision
            best_reason = rule["name"]

    return best_decision, best_reason
