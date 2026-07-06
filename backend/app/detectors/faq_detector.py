from app.detectors.schema_utils import json_ld_contains_type
from app.schemas import Issue

FAQ_KEYWORDS = [
    "faq",
    "faqs",
    "frequently asked questions",
    "common questions",
    "questions and answers",
]


def _has_faq_content(parsed: dict) -> bool:
    text_lower = parsed.get("text_lower", "")

    for keyword in FAQ_KEYWORDS:
        if keyword in text_lower:
            return True

    for heading in parsed.get("headings", []):
        heading_lower = heading.get("text", "").lower()
        for keyword in FAQ_KEYWORDS:
            if keyword in heading_lower:
                return True

    return False


def _has_faq_schema(parsed: dict) -> bool:
    return json_ld_contains_type(parsed.get("json_ld", []), {"FAQPage"})


def detect_faq_without_schema(parsed: dict, location: str) -> list[Issue]:
    if _has_faq_content(parsed) and not _has_faq_schema(parsed):
        return [
            Issue(
                id="missing_faq_schema",
                severity="high",
                category="structured_data",
                location=location,
                description=(
                    "FAQ content was detected, but no FAQPage JSON-LD"
                    " structured data was found."
                ),
            )
        ]
    return []
