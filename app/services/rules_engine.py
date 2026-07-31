from enum import Enum
from typing import Any, Optional


class Decision(str, Enum):
    APPROVE = "approve"
    REFER = "refer"
    DECLINE = "decline"


_SEVERITY = {Decision.APPROVE: 0, Decision.REFER: 1, Decision.DECLINE: 2}

_OPERATORS = {
    "eq": lambda actual, expected: actual == expected,
    "ne": lambda actual, expected: actual != expected,
    "gt": lambda actual, expected: actual is not None and actual > expected,
    "gte": lambda actual, expected: actual is not None and actual >= expected,
    "lt": lambda actual, expected: actual is not None and actual < expected,
    "lte": lambda actual, expected: actual is not None and actual <= expected,
    "in": lambda actual, expected: actual in expected,
    "not_in": lambda actual, expected: actual not in expected,
}


def _evaluate_condition(condition: dict, answers: dict[str, Any]) -> bool:
    if "all" in condition:
        return all(_evaluate_condition(sub, answers) for sub in condition["all"])
    if "any" in condition:
        return any(_evaluate_condition(sub, answers) for sub in condition["any"])

    operator = condition["operator"]
    if operator not in _OPERATORS:
        raise ValueError(f"Unsupported operator '{operator}'")

    actual = answers.get(condition["field"])
    return _OPERATORS[operator](actual, condition["value"])


def evaluate(rules_config: dict, answers: dict[str, Any]) -> tuple[Decision, Optional[str]]:
    """Evaluate every rule and return the most severe matching decision.

    decline > refer > approve. Ties keep the reason of the first rule that
    reached that severity level.
    """
    best_decision = Decision.APPROVE
    best_reason: Optional[str] = None

    for rule in rules_config.get("rules", []):
        if not _evaluate_condition(rule["when"], answers):
            continue

        decision = Decision(rule["decision"])
        if _SEVERITY[decision] > _SEVERITY[best_decision]:
            best_decision = decision
            best_reason = rule["name"]

    return best_decision, best_reason
