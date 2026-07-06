from pathlib import Path

from app.schemas import ExamplePage

SAMPLE_PAGES_DIR = Path(__file__).parent.parent / "sample_pages"

EXAMPLE_PAGES = {
    "faq-no-schema": {
        "filename": "faq_no_schema.html",
        "title": "FAQ without schema",
        "description": "FAQ content is visible, but FAQPage JSON-LD is missing.",
        "expected_issues": ["missing_fafq_schema"],
    },
    "saas-pricing-missing-schema": {
        "filename": "saas_pricing_missing_schema.html",
        "title": "SaaS pricing missing schema",
        "description": "Pricing page without Product/Service JSON-LD or policy links.",
        "expected_issues": [
            "missing_product_or_service_schema",
            "missing_policy_surface",
        ],
    },
    "good-agent-ready-page": {
        "filename": "good_agent_ready_page.html",
        "title": "Good agent-ready page",
        "description": "Page with proper structured data and clean heading hierarchy.",
        "expected_issues": [],
    },
    "bad-heading-structure": {
        "filename": "bad_heading_structure.html",
        "title": "Bad heading structure",
        "description": "Page with multiple H1s and heading hierarchy jumps.",
        "expected_issues": ["multiple_h1", "heading_hierarchy_jump"],
    },
}


def list_example_pages() -> list[ExamplePage]:
    """List all available example pages."""
    pages = []
    for example_id, info in EXAMPLE_PAGES.items():
        pages.append(
            ExamplePage(
                id=example_id,
                title=info["title"],
                description=info["description"],
                expected_issues=info["expected_issues"],
            )
        )
    return pages


def load_example_html(example_id: str) -> str:
    """Load HTML content for an example page."""
    if example_id not in EXAMPLE_PAGES:
        raise ValueError(f"Unknown example ID: {example_id}")

    filename = EXAMPLE_PAGES[example_id]["filename"]
    file_path = SAMPLE_PAGES_DIR / filename

    if not file_path.exists():
        raise FileNotFoundError(f"Sample page not found: {filename}")

    return file_path.read_text(encoding="utf-8")
