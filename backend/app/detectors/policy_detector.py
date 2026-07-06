from app.schemas import Issue

COMMERCIAL_KEYWORDS = [
    "pricing",
    "buy",
    "checkout",
    "subscribe",
    "subscription",
    "cart",
    "order",
    "payment",
    "plan",
    "plans",
]

POLICY_KEYWORDS = [
    "refund",
    "return",
    "returns",
    "shipping",
    "privacy",
    "privacy policy",
    "terms",
    "terms of service",
    "cancellation",
    "cancel",
]


def _has_commercial_intent(parsed: dict) -> bool:
    text_lower = parsed.get("text_lower", "")
    return any(kw in text_lower for kw in COMMERCIAL_KEYWORDS)


def _has_policy_surface(parsed: dict) -> bool:
    text_lower = parsed.get("text_lower", "")
    return any(kw in text_lower for kw in POLICY_KEYWORDS)


def detect_missing_policy_surface(parsed: dict, location: str) -> list[Issue]:
    if _has_commercial_intent(parsed) and not _has_policy_surface(parsed):
        return [
            Issue(
                id="missing_policy_surface",
                severity="medium",
                location=location,
                description="Commercial intent was detected, but refund, returns, shipping, privacy, terms, or cancellation information is not clearly surfaced.",
            )
        ]
    return []
