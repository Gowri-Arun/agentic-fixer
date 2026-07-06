from app.detectors.faq_detector import detect_faq_without_schema
from app.detectors.heading_detector import detect_heading_issues
from app.detectors.policy_detector import detect_missing_policy_surface
from app.detectors.pricing_detector import detect_pricing_without_schema
from app.detectors.structured_data_detector import detect_invalid_json_ld
from app.schemas import Issue


def run_detectors(parsed: dict, location: str) -> list[Issue]:
    issues: list[Issue] = []
    issues.extend(detect_faq_without_schema(parsed, location))
    issues.extend(detect_pricing_without_schema(parsed, location))
    issues.extend(detect_missing_policy_surface(parsed, location))
    issues.extend(detect_heading_issues(parsed, location))
    issues.extend(detect_invalid_json_ld(parsed, location))
    return issues
