from pathlib import Path

from app.evaluation.models import PageType, SiteConfig
from scripts.evaluate_sites import _filter_sites, _parse_args

CORPUS = Path(__file__).parent.parent / "evaluation" / "sites.yml"


def test_parse_args_default():
    import sys

    original_argv = sys.argv
    sys.argv = ["evaluate_sites"]
    try:
        args = _parse_args()
        assert args.corpus is not None
        assert args.concurrency == 4
        assert args.max_attempts == 3
        assert args.target_stack == "nextjs-13"
        assert args.verbose is False
    finally:
        sys.argv = original_argv


def test_parse_args_custom():
    import sys

    original_argv = sys.argv
    sys.argv = [
        "evaluate_sites",
        "--corpus",
        "custom.yml",
        "--output",
        "custom_output",
        "--concurrency",
        "8",
        "--max-attempts",
        "5",
        "--target-stack",
        "react-spa",
        "--verbose",
    ]
    try:
        args = _parse_args()
        assert str(args.corpus) == "custom.yml"
        assert str(args.output) == "custom_output"
        assert args.concurrency == 8
        assert args.max_attempts == 5
        assert args.target_stack == "react-spa"
        assert args.verbose is True
    finally:
        sys.argv = original_argv


def test_parse_args_page_type_filter():
    import sys

    original_argv = sys.argv
    sys.argv = ["evaluate_sites", "--page-type", "pricing"]
    try:
        args = _parse_args()
        assert args.page_type == "pricing"
    finally:
        sys.argv = original_argv


def test_parse_args_tag_filter():
    import sys

    original_argv = sys.argv
    sys.argv = ["evaluate_sites", "--tag", "saas"]
    try:
        args = _parse_args()
        assert args.tag == "saas"
    finally:
        sys.argv = original_argv


def test_parse_args_max_sites():
    import sys

    original_argv = sys.argv
    sys.argv = ["evaluate_sites", "--max-sites", "5"]
    try:
        args = _parse_args()
        assert args.max_sites == 5
    finally:
        sys.argv = original_argv


def test_parse_args_disabled_flag():
    import sys

    original_argv = sys.argv
    sys.argv = ["evaluate_sites", "--disabled"]
    try:
        args = _parse_args()
        assert args.disabled is True
    finally:
        sys.argv = original_argv


def test_filter_sites_by_page_type():
    sites = [
        SiteConfig(
            name="Pricing",
            url="https://pricing.example.com",
            page_type=PageType.PRICING,
            expected_signals=[{"description": "pricing"}],
        ),
        SiteConfig(
            name="FAQ",
            url="https://faq.example.com",
            page_type=PageType.FAQ,
            expected_signals=[{"description": "faq"}],
        ),
    ]

    filtered = _filter_sites(sites, page_type="pricing")
    assert len(filtered) == 1
    assert filtered[0].page_type == PageType.PRICING


def test_filter_sites_by_tag():
    sites = [
        SiteConfig(
            name="SaaS",
            url="https://saas.example.com",
            page_type=PageType.SERVICE,
            expected_signals=[{"description": "service"}],
            tags=["saas", "pricing"],
        ),
        SiteConfig(
            name="Blog",
            url="https://blog.example.com",
            page_type=PageType.GENERAL,
            expected_signals=[{"description": "general"}],
            tags=["blog"],
        ),
    ]

    filtered = _filter_sites(sites, tag="saas")
    assert len(filtered) == 1
    assert "saas" in filtered[0].tags


def test_filter_sites_max_sites():
    sites = [
        SiteConfig(
            name=f"Site {i}",
            url=f"https://site{i}.example.com",
            page_type=PageType.GENERAL,
            expected_signals=[{"description": "test"}],
        )
        for i in range(10)
    ]

    filtered = _filter_sites(sites, max_sites=3)
    assert len(filtered) == 3


def test_filter_sites_no_filters():
    sites = [
        SiteConfig(
            name="Site A",
            url="https://a.example.com",
            page_type=PageType.PRICING,
            expected_signals=[{"description": "test"}],
        ),
        SiteConfig(
            name="Site B",
            url="https://b.example.com",
            page_type=PageType.FAQ,
            expected_signals=[{"description": "test"}],
        ),
    ]

    filtered = _filter_sites(sites)
    assert len(filtered) == 2


def test_corpus_exists():
    import sys

    original_argv = sys.argv
    sys.argv = ["evaluate_sites"]
    try:
        args = _parse_args()
        assert args.corpus.exists()
    finally:
        sys.argv = original_argv
