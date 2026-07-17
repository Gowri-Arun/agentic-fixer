from enum import Enum

from pydantic import BaseModel, HttpUrl


class PageType(str, Enum):
    """Page types for evaluation sites."""

    PRICING = "pricing"
    FAQ = "faq"
    ECOMMERCE = "ecommerce"
    SERVICE = "service"
    GENERAL = "general"


class ExpectedSignal(BaseModel):
    """Broad expected page characteristics (not exact issue IDs)."""

    description: str


class SiteConfig(BaseModel):
    """Configuration for a real-site evaluation entry."""

    name: str
    url: HttpUrl
    page_type: PageType
    expected_signals: list[ExpectedSignal]
    tags: list[str] = []
    enabled: bool = True
    notes: str = ""


class EvaluationConfig(BaseModel):
    """Root configuration for the evaluation corpus."""

    sites: list[SiteConfig]
