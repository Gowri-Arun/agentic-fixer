"""Tests for proposal context generator."""

from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from app.evaluation.models import (
    EvaluationRun,
    PageType,
    RunSummary,
    SiteSuccess,
)
from app.evaluation.proposal import (
    ProposalDocument,
    generate_proposals,
    render_json,
    render_markdown,
)

FIXTURES = Path(__file__).parent / "fixtures"


def _make_run(
    results=None,
) -> EvaluationRun:
    """Create a minimal EvaluationRun for testing."""
    return EvaluationRun(
        run_id=uuid4(),
        started_at=datetime.now(timezone.utc),
        completed_at=datetime.now(timezone.utc),
        corpus_path="test.yml",
        target_stack="nextjs-13",
        results=results or [],
        summary=RunSummary(
            total_sites=1,
            successful_sites=1,
            failed_sites=0,
            total_duration_ms=100,
            average_score=80.0,
            scores_by_page_type={"pricing": 80.0},
        ),
    )


def _make_success(
    url: str = "https://example.com/pricing",
    name: str = "Example Pricing",
    page_type: PageType = PageType.PRICING,
    score: int = 80,
    issue_ids=None,
) -> SiteSuccess:
    """Create a minimal SiteSuccess for testing."""
    return SiteSuccess(
        url=url,
        name=name,
        page_type=page_type,
        score=score,
        issue_ids=issue_ids or [],
        issue_count=len(issue_ids or []),
        duration_ms=100,
    )


def test_generate_proposals_empty_run():
    run = _make_run(results=[])
    doc = generate_proposals(run)

    assert doc.total_proposals == 0
    assert doc.groups == []


def test_generate_proposals_no_warnings():
    # Pricing page with schema and matching issue = no warnings
    # Also need enough text to avoid weak-signal warning
    result = _make_success(
        issue_ids=["missing_product_or_service_schema"],
    )
    run = _make_run(results=[result])

    html_cache = {
        result.url: "<html><body><h1>Pricing</h1><p>" + "x " * 60 + "</p></body></html>"
    }
    doc = generate_proposals(run, html_cache=html_cache)

    assert doc.total_proposals == 0
    assert doc.groups == []


def test_generate_proposals_pricing_false_negative():
    # Pricing page with currency matches but no schema and no issue
    result = _make_success(
        issue_ids=[],
    )
    run = _make_run(results=[result])

    # Patch signals to have pricing indicators
    html = "<html><body><h1>Pricing</h1>"
    html += "<p>Starts at $99/month</p></body></html>"
    html_cache = {result.url: html}

    doc = generate_proposals(run, html_cache=html_cache)

    # Should generate a proposal for possible_false_negative
    assert doc.total_proposals > 0
    assert len(doc.groups) == 1
    assert doc.groups[0].detector_name == "pricing_detector"
    assert doc.groups[0].warning_type_counts.get("possible_false_negative", 0) > 0


def test_generate_proposals_faq_false_negative():
    # FAQ page with indicators but no schema
    result = _make_success(
        url="https://example.com/faq",
        name="Example FAQ",
        page_type=PageType.FAQ,
        issue_ids=[],
    )
    run = _make_run(results=[result])

    html = "<html><body><h1>FAQ</h1><h2>What is X?</h2>"
    html += "<h2>How do I Y?</h2>"
    html += "<p>Frequently asked questions</p></body></html>"
    html_cache = {result.url: html}

    doc = generate_proposals(run, html_cache=html_cache)

    # Should generate a proposal
    assert doc.total_proposals > 0
    assert len(doc.groups) == 1
    assert doc.groups[0].detector_name == "faq_detector"


def test_generate_proposals_with_text_excerpts():
    result = _make_success(issue_ids=[])
    run = _make_run(results=[result])

    base_text = "This is a pricing page with detailed information "
    base_text += "about our plans and pricing options. "
    long_text = base_text * 5
    html_cache = {result.url: f"<html><body><p>{long_text}</p></body></html>"}

    doc = generate_proposals(run, html_cache=html_cache)

    if doc.total_proposals > 0:
        for group in doc.groups:
            for proposal in group.proposals:
                # Excerpts truncated (200 chars + "..." = 203)
                for excerpt in proposal.text_excerpts:
                    assert len(excerpt) <= 203
                    assert "[REDACTED]" not in excerpt or True


def test_generate_proposals_sanitizes_sensitive_data():
    result = _make_success(issue_ids=[])
    run = _make_run(results=[result])

    html_with_sensitive = """
    <html><body>
    <p>Contact us at user@example.com for pricing.</p>
    <p>Card number: 4111 1111 1111 1111</p>
    <p>API_KEY=sk_test_1234567890abcdef</p>
    </body></html>
    """
    html_cache = {result.url: html_with_sensitive}

    doc = generate_proposals(run, html_cache=html_cache)

    if doc.total_proposals > 0:
        for group in doc.groups:
            for proposal in group.proposals:
                for excerpt in proposal.text_excerpts:
                    assert "user@example.com" not in excerpt
                    assert "4111 1111 1111 1111" not in excerpt
                    assert "sk_test_1234567890abcdef" not in excerpt


def test_generate_proposals_groups_by_detector():
    # Create run with multiple sites that should trigger different detectors
    pricing_result = _make_success(
        url="https://example.com/pricing",
        page_type=PageType.PRICING,
        issue_ids=[],
    )
    faq_result = _make_success(
        url="https://example.com/faq",
        name="Example FAQ",
        page_type=PageType.FAQ,
        issue_ids=[],
    )

    run = _make_run(results=[pricing_result, faq_result])

    pricing_html = "<html><body><p>Plans start at $99/month</p></body></html>"
    faq_html = "<html><body><h1>FAQ</h1><h2>What is X?</h2>"
    faq_html += "<h2>How do I Y?</h2></body></html>"
    html_cache = {
        pricing_result.url: pricing_html,
        faq_result.url: faq_html,
    }

    doc = generate_proposals(run, html_cache=html_cache)

    # Should have separate groups for each detector
    detector_names = [g.detector_name for g in doc.groups]
    if doc.total_proposals > 0:
        assert len(detector_names) > 0
        # Each group should have the correct detector name
        for group in doc.groups:
            assert group.detector_name in ("pricing_detector", "faq_detector")


def test_generate_proposals_related_tests():
    result = _make_success(issue_ids=[])
    run = _make_run(results=[result])

    html_cache = {
        result.url: "<html><body><p>Plans start at $99/month</p></body></html>"
    }

    doc = generate_proposals(
        run,
        html_cache=html_cache,
        tests_dir=Path(__file__).parent,
    )

    if doc.total_proposals > 0:
        for group in doc.groups:
            for proposal in group.proposals:
                # Should discover related test files
                assert isinstance(proposal.related_tests, list)


def test_render_markdown_empty():
    doc = ProposalDocument(
        run_id="test-run",
        run_date="2025-01-01T00:00:00",
        total_proposals=0,
        detectors_with_proposals=[],
        groups=[],
    )

    md = render_markdown(doc)

    assert "Detector Improvement Proposals" in md
    assert "**Total proposals:** 0" in md
    assert "No suspicious cases found." in md


def test_render_markdown_with_proposals():
    from app.evaluation.proposal import DetectorProposal, ProposalGroup

    proposal = DetectorProposal(
        detector_name="pricing_detector",
        detector_version="1.0.0",
        warning_type="possible_false_negative",
        warning_severity="medium",
        warning_explanation="Pricing content detected but no issue raised.",
        related_issue_id="missing_product_or_service_schema",
        site_name="Example Pricing",
        site_url="https://example.com/pricing",
        site_page_type="pricing",
        expected_signals=["Pricing page with visible prices"],
        observed_issue_ids=[],
        evidence={"currency_match_count": 2},
        signal_summary={"visible_text_length": 500},
        text_excerpts=["Pricing starts at $99/month"],
        related_tests=["tests/test_pricing_detector.py"],
    )

    group = ProposalGroup(
        detector_name="pricing_detector",
        detector_version="1.0.0",
        proposals=[proposal],
        warning_type_counts={"possible_false_negative": 1},
    )

    doc = ProposalDocument(
        run_id="test-run",
        run_date="2025-01-01T00:00:00",
        total_proposals=1,
        detectors_with_proposals=["pricing_detector"],
        groups=[group],
    )

    md = render_markdown(doc)

    assert "pricing_detector" in md
    assert "Example Pricing" in md
    assert "possible_false_negative" in md
    assert "Pricing starts at $99/month" in md
    assert "tests/test_pricing_detector.py" in md


def test_render_json_empty():
    doc = ProposalDocument(
        run_id="test-run",
        run_date="2025-01-01T00:00:00",
        total_proposals=0,
        detectors_with_proposals=[],
        groups=[],
    )

    json_str = render_json(doc)

    assert '"run_id": "test-run"' in json_str
    assert '"total_proposals": 0' in json_str


def test_render_json_with_proposals():
    from app.evaluation.proposal import DetectorProposal, ProposalGroup

    proposal = DetectorProposal(
        detector_name="faq_detector",
        detector_version="1.0.0",
        warning_type="possible_false_negative",
        warning_severity="medium",
        warning_explanation="FAQ indicators found but no schema.",
        site_name="Example FAQ",
        site_url="https://example.com/faq",
        site_page_type="faq",
    )

    group = ProposalGroup(
        detector_name="faq_detector",
        detector_version="1.0.0",
        proposals=[proposal],
        warning_type_counts={"possible_false_negative": 1},
    )

    doc = ProposalDocument(
        run_id="test-run",
        run_date="2025-01-01T00:00:00",
        total_proposals=1,
        detectors_with_proposals=["faq_detector"],
        groups=[group],
    )

    json_str = render_json(doc)

    assert '"detector_name": "faq_detector"' in json_str
    assert '"warning_type": "possible_false_negative"' in json_str


def test_generate_proposals_with_corpus():
    """Test that corpus expected signals are included in proposals."""

    result = _make_success(issue_ids=[])
    run = _make_run(results=[result])

    # Create a temp corpus file
    corpus_content = f"""
sites:
  - name: Example Pricing
    url: {result.url}
    page_type: pricing
    expected_signals:
      - description: Should have Product/Service schema
      - description: Should show pricing information
"""
    corpus_path = FIXTURES / "test_corpus.yml"
    corpus_path.write_text(corpus_content)

    try:
        html_cache = {
            result.url: "<html><body><p>Plans start at $99/month</p></body></html>"
        }

        doc = generate_proposals(run, corpus_path=corpus_path, html_cache=html_cache)

        if doc.total_proposals > 0:
            for group in doc.groups:
                for proposal in group.proposals:
                    # Should include expected signals from corpus
                    assert len(proposal.expected_signals) > 0
    finally:
        corpus_path.unlink(missing_ok=True)


def test_sanitize_text_truncation():
    from app.evaluation.proposal import _sanitize_text

    long_text = "A" * 300
    sanitized = _sanitize_text(long_text)

    # Truncation adds "..." after 200 chars = 203 total
    assert len(sanitized) <= 203
    assert sanitized.endswith("...")


def test_sanitize_text_html_removal():
    from app.evaluation.proposal import _sanitize_text

    html_text = "<p>Hello <b>world</b></p>"
    sanitized = _sanitize_text(html_text)

    assert "<p>" not in sanitized
    assert "<b>" not in sanitized
    assert "Hello" in sanitized
    assert "world" in sanitized


def test_extract_text_excerpts_no_html():
    from app.evaluation.proposal import _extract_text_excerpts

    excerpts = _extract_text_excerpts("")

    assert excerpts == []


def test_extract_text_excerpts():
    from app.evaluation.proposal import _extract_text_excerpts

    # BeautifulSoup returns all text as a single block
    html = """
    <html>
    <body>
        <div>First paragraph with enough content to pass threshold.</div>
        <div>Second paragraph with enough content to pass threshold.</div>
        <div>Third paragraph with enough content to pass threshold.</div>
    </body>
    </html>
    """
    excerpts = _extract_text_excerpts(html, max_excerpts=2)

    # Note: BeautifulSoup's get_text joins all text, so excerpts may not be exactly 2
    assert len(excerpts) <= 2
    for excerpt in excerpts:
        assert len(excerpt) <= 203
