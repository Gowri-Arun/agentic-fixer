from app.reporting.metadata import build_audit_metadata


def test_metadata_includes_url():
    metadata = build_audit_metadata(
        url="https://example.com",
        location="/",
        target_stack="nextjs-13",
        issue_count=0,
        fix_count=0,
    )
    assert metadata.url == "https://example.com"


def test_metadata_includes_location():
    metadata = build_audit_metadata(
        url="https://example.com",
        location="/pricing",
        target_stack="nextjs-13",
        issue_count=0,
        fix_count=0,
    )
    assert metadata.location == "/pricing"


def test_metadata_includes_target_stack():
    metadata = build_audit_metadata(
        url="https://example.com",
        location="/",
        target_stack="react-spa",
        issue_count=0,
        fix_count=0,
    )
    assert metadata.target_stack == "react-spa"


def test_metadata_includes_issue_count():
    metadata = build_audit_metadata(
        url="https://example.com",
        location="/",
        target_stack="nextjs-13",
        issue_count=5,
        fix_count=3,
    )
    assert metadata.issue_count == 5


def test_metadata_includes_fix_count():
    metadata = build_audit_metadata(
        url="https://example.com",
        location="/",
        target_stack="nextjs-13",
        issue_count=5,
        fix_count=3,
    )
    assert metadata.fix_count == 3


def test_metadata_checked_at_is_non_empty():
    metadata = build_audit_metadata(
        url="https://example.com",
        location="/",
        target_stack="nextjs-13",
        issue_count=0,
        fix_count=0,
    )
    assert metadata.checked_at
    assert len(metadata.checked_at) > 0


def test_metadata_detectors_run_includes_expected_detectors():
    metadata = build_audit_metadata(
        url="https://example.com",
        location="/",
        target_stack="nextjs-13",
        issue_count=0,
        fix_count=0,
    )
    assert "faq" in metadata.detectors_run
    assert "pricing" in metadata.detectors_run
    assert "policy" in metadata.detectors_run
    assert "headings" in metadata.detectors_run
    assert "structured_data" in metadata.detectors_run
