from datetime import datetime, timezone

from app.schemas import AuditMetadata, TargetStack

DETECTORS_RUN = [
    "faq",
    "pricing",
    "policy",
    "headings",
    "structured_data",
]


def build_audit_metadata(
    url: str,
    location: str,
    target_stack: TargetStack,
    issue_count: int,
    fix_count: int,
    detector_results: list[dict] | None = None,
) -> AuditMetadata:
    """
    Build audit metadata for the response.

    Args:
        url: The URL that was analyzed
        location: The URL path/location
        target_stack: The target stack for fixes
        issue_count: Number of issues found
        fix_count: Number of fixes generated
        detector_results: Optional list of detector result dicts

    Returns:
        AuditMetadata object with all required fields
    """
    checked_at = datetime.now(timezone.utc).isoformat()

    return AuditMetadata(
        url=url,
        location=location,
        target_stack=target_stack,
        checked_at=checked_at,
        issue_count=issue_count,
        fix_count=fix_count,
        detectors_run=DETECTORS_RUN,
        detector_results=detector_results,
    )
