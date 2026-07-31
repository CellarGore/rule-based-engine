from typing import Any

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


def evaluate_condition(condition: dict, answers: dict[str, Any]) -> bool:
    """Evaluate a 'when' condition (leaf field/operator/value, or an all/any group) against answers."""
    if "all" in condition:
        return all(evaluate_condition(sub, answers) for sub in condition["all"])
    if "any" in condition:
        return any(evaluate_condition(sub, answers) for sub in condition["any"])

    operator = condition["operator"]
    if operator not in _OPERATORS:
        raise ValueError(f"Unsupported operator '{operator}'")

    actual = answers.get(condition["field"])
    return _OPERATORS[operator](actual, condition["value"])
