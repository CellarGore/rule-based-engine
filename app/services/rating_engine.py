from typing import Any

from app.services.conditions import evaluate_condition


class PremiumCalculationError(Exception):
    """Raised when the given answers are insufficient/invalid to calculate a premium."""


_ACTIONS = {
    "multiplier": lambda premium, value: premium * value,
}


def calculate_premium(rating_config: dict, answers: dict[str, Any]) -> float:
    business_type = answers.get("business_type")
    base_rates = rating_config.get("base_rates", {})
    if business_type not in base_rates:
        raise PremiumCalculationError(f"No base rate configured for business_type '{business_type}'")

    annual_payroll = answers.get("annual_payroll")
    if not isinstance(annual_payroll, (int, float)) or isinstance(annual_payroll, bool):
        raise PremiumCalculationError("Answer 'annual_payroll' must be a number to calculate a premium")

    premium = base_rates[business_type] * (annual_payroll / 100)

    for adjustment in rating_config.get("adjustments", []):
        if not evaluate_condition(adjustment["when"], answers):
            continue

        action = adjustment["action"]
        action_type = action["type"]
        if action_type not in _ACTIONS:
            raise ValueError(f"Unsupported adjustment action type '{action_type}'")

        premium = _ACTIONS[action_type](premium, action["value"])

    return round(premium, 2)
