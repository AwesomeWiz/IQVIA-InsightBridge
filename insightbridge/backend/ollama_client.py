"""Optional Ollama intent classification. It never creates SQL."""

import json
import os
from urllib.error import URLError
from urllib.request import Request, urlopen


ALLOWED_INTENTS = {
    "customers_by_plan_location",
    "revenue_by_quarter",
    "top_customers",
    "customer_health",
    "sales_pipeline",
    "subscriptions_by_plan",
    "marketing_performance",
}
ALLOWED_KEYS = {"intent", "state", "plan_tier", "year", "churn_risks", "stage", "open_only"}


def interpret_with_ollama(question: str) -> dict | None:
    if os.getenv("OLLAMA_ENABLED", "false").lower() != "true":
        return None

    prompt = f"""Classify this business question as JSON only.
Allowed intents: {', '.join(sorted(ALLOWED_INTENTS))}.
Optional fields: state, plan_tier, year, churn_risks (array), stage, open_only.
Do not generate SQL or explanations. Omit unknown fields.
Question: {question}
"""
    body = json.dumps({"model": "qwen3:1.7b", "prompt": prompt, "stream": False}).encode()
    request = Request(
        "http://localhost:11434/api/generate",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=2) as response:
            payload = json.loads(response.read().decode("utf-8"))
        model_result = json.loads(payload["response"].strip())
    except (URLError, TimeoutError, json.JSONDecodeError, KeyError, TypeError, ValueError):
        return None

    if not isinstance(model_result, dict) or model_result.get("intent") not in ALLOWED_INTENTS:
        return None
    if any(key not in ALLOWED_KEYS for key in model_result):
        return None
    return {**model_result, "parser": "ollama"}
