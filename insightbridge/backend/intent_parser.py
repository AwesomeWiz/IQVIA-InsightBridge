"""Deterministic natural-language parsing for the supported questions."""

import re


STATES = [
    "Alabama", "Alaska", "Arizona", "Arkansas", "California", "Colorado",
    "Connecticut", "Delaware", "Florida", "Georgia", "Hawaii", "Idaho",
    "Illinois", "Indiana", "Iowa", "Kansas", "Kentucky", "Louisiana",
    "Maine", "Maryland", "Massachusetts", "Michigan", "Minnesota",
    "Mississippi", "Missouri", "Montana", "Nebraska", "Nevada",
    "New Hampshire", "New Jersey", "New Mexico", "New York",
    "North Carolina", "North Dakota", "Ohio", "Oklahoma", "Oregon",
    "Pennsylvania", "Rhode Island", "South Carolina", "South Dakota",
    "Tennessee", "Texas", "Utah", "Vermont", "Virginia", "Washington",
    "Washington DC", "West Virginia", "Wisconsin", "Wyoming",
]
PLAN_TIERS = ["free", "basic", "professional", "premium", "enterprise"]
CHURN_RISKS = ["low", "medium", "high", "critical"]
SALES_STAGES = ["lead", "qualified", "proposal", "negotiation", "closed_won", "closed_lost"]


def _extract_choice(question: str, choices: list[str]) -> str | None:
    normalized = re.sub(r"[-\s]+", "_", question.lower())
    for choice in sorted(choices, key=len, reverse=True):
        candidate = re.sub(r"[-\s]+", "_", choice.lower())
        if re.search(rf"(?:^|_){re.escape(candidate)}(?:_|$)", normalized):
            return choice
    return None


def parse_question(question: str) -> dict:
    text = " ".join(question.lower().split())
    result = {"parser": "rules"}

    if re.search(r"\bbest\s+(customers?|clients?|accounts?)\b", text):
        return {
            **result,
            "intent": "clarification",
            "clarification": (
                "What do you mean by best: highest revenue, highest health score, "
                "highest usage, or highest renewal probability?"
            ),
        }

    state = _extract_choice(question, STATES)
    plan_tier = _extract_choice(question, PLAN_TIERS)
    year_match = re.search(r"\b(20\d{2})\b", text)
    risks = [risk for risk in CHURN_RISKS if re.search(rf"\b{risk}\b", text)]
    stage = _extract_choice(question, SALES_STAGES)

    customer_words = any(word in text for word in ("customer", "subscriber", "client", "account"))
    plan_words = any(word in text for word in ("plan", "subscription", "subscriber")) or bool(plan_tier)

    if customer_words and plan_words and (state or plan_tier):
        return {**result, "intent": "customers_by_plan_location", "state": state, "plan_tier": plan_tier}
    if "revenue" in text and any(word in text for word in ("quarter", "quarterly", "q1", "q2", "q3", "q4")):
        return {**result, "intent": "revenue_by_quarter", "year": int(year_match.group()) if year_match else None}
    if customer_words and any(word in text for word in ("churn", "health", "renewal", "risk")):
        return {**result, "intent": "customer_health", "churn_risks": risks}
    if any(word in text for word in ("opportunit", "pipeline", "deal")):
        return {**result, "intent": "sales_pipeline", "stage": stage, "open_only": "open" in text}
    if plan_words and any(word in text for word in ("most", "count", "breakdown", "how many", "popular")):
        return {**result, "intent": "subscriptions_by_plan"}
    if customer_words and "revenue" in text and any(word in text for word in ("top", "highest", "largest")):
        return {**result, "intent": "top_customers"}
    if any(word in text for word in ("campaign", "marketing")) and any(
        word in text for word in ("performance", "conversion", "spend", "roi")
    ):
        return {**result, "intent": "marketing_performance"}

    return {
        **result,
        "intent": "unsupported",
        "clarification": (
            "I can answer questions about customers and plans, quarterly revenue, "
            "customer health, sales opportunities, subscriptions by plan, and marketing performance."
        ),
    }
