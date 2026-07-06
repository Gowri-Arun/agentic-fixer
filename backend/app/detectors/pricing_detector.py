import re

from app.detectors.schema_utils import json_ld_contains_type
from app.schemas import Issue

PRICING_KEYWORDS = [
    "pricing",
    "plans",
    "subscription",
    "monthly",
    "yearly",
    "per month",
    "per year",
    "starter",
    "pro plan",
    "enterprise",
]

CURRENCY_PATTERNS = [
    r"\$\d+",
    r"₹\d+",
    r"€\d+",
    r"£\d+",
    r"USD\s*\d+",
    r"INR\s*\d+",
    r"EUR\s*\d+",
    r"GBP\s*\d+",
]


def _has_pricing_content(parsed: dict) -> bool:
    text_lower = parsed.get("text_lower", "")

    has_keyword = any(kw in text_lower for kw in PRICING_KEYWORDS)
    has_currency = any(
        re.search(pat, parsed.get("text", "")) for pat in CURRENCY_PATTERNS
    )

    return has_keyword and has_currency


def _has_product_or_service_schema(parsed: dict) -> bool:
    return json_ld_contains_type(parsed.get("json_ld", []), {"Product", "Service"})


def detect_pricing_without_schema(parsed: dict, location: str) -> list[Issue]:
    if _has_pricing_content(parsed) and not _has_product_or_service_schema(parsed):
        return [
            Issue(
                id="missing_product_or_service_schema",
                severity="high",
                category="structured_data",
                location=location,
                description=(
                    "Pricing or commercial offering content was detected,"
                    " but no Product or Service JSON-LD structured"
                    " data was found."
                ),
            )
        ]
    return []
