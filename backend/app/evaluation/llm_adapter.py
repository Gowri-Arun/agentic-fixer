"""Optional LLM adapter for detector-improvement suggestions.

Submits sanitised proposal context to a configurable LLM provider
and saves proposed changes for human review.  This module is:

- Disabled by default (requires explicit provider + API key).
- Never executes generated code.
- Never edits detector files automatically.
- Never commits changes or opens pull requests.

All LLM output is treated as untrusted suggestions.

Usage:
    python -m scripts.propose --llm --provider openai
"""

from __future__ import annotations

import json
import os
from abc import ABC, abstractmethod

from pydantic import BaseModel, Field

from app.evaluation.proposal import DetectorProposal

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

ENV_PROVIDER = "DETECTION_LLM_PROVIDER"
ENV_API_KEY = "DETECTION_LLM_API_KEY"
ENV_MODEL = "DETECTION_LLM_MODEL"
ENV_BASE_URL = "DETECTION_LLM_BASE_URL"

# Default models per provider
DEFAULT_MODELS: dict[str, str] = {
    "openai": "gpt-4o-mini",
    "anthropic": "claude-3-haiku-20240307",
    "ollama": "llama3.2",
}

# Provider-specific defaults
DEFAULT_BASE_URLS: dict[str, str] = {
    "openai": "https://api.openai.com/v1",
    "anthropic": "https://api.anthropic.com",
    "ollama": "http://localhost:11434",
}

# ---------------------------------------------------------------------------
# Structured output model
# ---------------------------------------------------------------------------


class DetectorSuggestion(BaseModel):
    """Structured LLM suggestion for a single detector proposal."""

    likely_cause: str = Field(
        description="Likely cause of the false positive or false negative"
    )
    proposed_rule_adjustment: str = Field(
        description="Suggested change to detection rules or thresholds"
    )
    expected_risks: list[str] = Field(
        default_factory=list,
        description="Potential risks or side effects of the change",
    )
    tests_to_add: list[str] = Field(
        default_factory=list,
        description="Suggested new test cases",
    )
    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="Confidence level (0.0 to 1.0)",
    )
    uncertainty: str = Field(description="What the model is uncertain about")


class LLMProposalResult(BaseModel):
    """Result from LLM analysis of a single proposal."""

    proposal_id: str
    detector_name: str
    site_name: str
    suggestion: DetectorSuggestion
    raw_response: str = ""
    provider: str = ""
    model: str = ""


# ---------------------------------------------------------------------------
# Provider interface
# ---------------------------------------------------------------------------


class LLMProvider(ABC):
    """Abstract interface for LLM providers."""

    @abstractmethod
    def is_available(self) -> bool:
        """Check if the provider is configured and available."""

    @abstractmethod
    def generate_suggestion(self, prompt: str) -> str:
        """Send a prompt to the LLM and return the raw response.

        Raises:
            LLMProviderError: If the request fails.
        """


class LLMProviderError(Exception):
    """Raised when an LLM provider request fails."""


# ---------------------------------------------------------------------------
# Provider implementations
# ---------------------------------------------------------------------------


class OpenAIProvider(LLMProvider):
    """OpenAI API provider."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        base_url: str | None = None,
    ):
        self.api_key = api_key or os.environ.get(ENV_API_KEY, "")
        self.model = model or os.environ.get(ENV_MODEL, DEFAULT_MODELS["openai"])
        self.base_url = base_url or os.environ.get(
            ENV_BASE_URL, DEFAULT_BASE_URLS["openai"]
        )

    def is_available(self) -> bool:
        return bool(self.api_key)

    def generate_suggestion(self, prompt: str) -> str:
        if not self.api_key:
            raise LLMProviderError("OpenAI API key not configured")

        try:
            import httpx
        except ImportError as exc:
            raise LLMProviderError(
                "httpx package required for OpenAI provider"
            ) from exc

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are an expert in web accessibility and SEO detection. "
                        "Analyse the provided detector proposal context and return "
                        "a structured JSON response with the specified fields."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.3,
            "max_tokens": 1024,
        }

        try:
            response = httpx.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=30.0,
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]
        except Exception as exc:
            raise LLMProviderError(f"OpenAI request failed: {exc}") from exc


class AnthropicProvider(LLMProvider):
    """Anthropic Claude API provider."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
    ):
        self.api_key = api_key or os.environ.get(ENV_API_KEY, "")
        self.model = model or os.environ.get(ENV_MODEL, DEFAULT_MODELS["anthropic"])

    def is_available(self) -> bool:
        return bool(self.api_key)

    def generate_suggestion(self, prompt: str) -> str:
        if not self.api_key:
            raise LLMProviderError("Anthropic API key not configured")

        try:
            import httpx
        except ImportError as exc:
            raise LLMProviderError(
                "httpx package required for Anthropic provider"
            ) from exc

        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        }

        payload = {
            "model": self.model,
            "max_tokens": 1024,
            "system": (
                "You are an expert in web accessibility and SEO detection. "
                "Analyse the provided detector proposal context and return "
                "a structured JSON response with the specified fields."
            ),
            "messages": [{"role": "user", "content": prompt}],
        }

        try:
            response = httpx.post(
                f"{DEFAULT_BASE_URLS['anthropic']}/v1/messages",
                headers=headers,
                json=payload,
                timeout=30.0,
            )
            response.raise_for_status()
            data = response.json()
            return data["content"][0]["text"]
        except Exception as exc:
            raise LLMProviderError(f"Anthropic request failed: {exc}") from exc


class OllamaProvider(LLMProvider):
    """Ollama local model provider."""

    def __init__(
        self,
        model: str | None = None,
        base_url: str | None = None,
    ):
        self.model = model or os.environ.get(ENV_MODEL, DEFAULT_MODELS["ollama"])
        self.base_url = base_url or os.environ.get(
            ENV_BASE_URL, DEFAULT_BASE_URLS["ollama"]
        )

    def is_available(self) -> bool:
        try:
            import httpx

            response = httpx.get(f"{self.base_url}/api/tags", timeout=5.0)
            return response.status_code == 200
        except Exception:
            return False

    def generate_suggestion(self, prompt: str) -> str:
        try:
            import httpx
        except ImportError as exc:
            raise LLMProviderError(
                "httpx package required for Ollama provider"
            ) from exc

        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0.3, "num_predict": 1024},
        }

        try:
            response = httpx.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=60.0,
            )
            response.raise_for_status()
            data = response.json()
            return data["response"]
        except Exception as exc:
            raise LLMProviderError(f"Ollama request failed: {exc}") from exc


# ---------------------------------------------------------------------------
# Provider factory
# ---------------------------------------------------------------------------

_PROVIDERS: dict[str, type[LLMProvider]] = {
    "openai": OpenAIProvider,
    "anthropic": AnthropicProvider,
    "ollama": OllamaProvider,
}


def get_provider(name: str | None = None) -> LLMProvider:
    """Get an LLM provider by name.

    Defaults to the provider specified in DETECTION_LLM_PROVIDER env var,
    or 'openai' if not set.
    """
    provider_name = name or os.environ.get(ENV_PROVIDER, "openai")
    provider_cls = _PROVIDERS.get(provider_name)
    if provider_cls is None:
        raise ValueError(
            f"Unknown provider: {provider_name}. "
            f"Available: {', '.join(_PROVIDERS.keys())}"
        )
    return provider_cls()


# ---------------------------------------------------------------------------
# Prompt construction
# ---------------------------------------------------------------------------


def build_suggestion_prompt(proposal: DetectorProposal) -> str:
    """Build a structured prompt for a single proposal.

    Returns a prompt that asks the LLM to return JSON with:
    - likely_cause
    - proposed_rule_adjustment
    - expected_risks
    - tests_to_add
    - confidence
    - uncertainty
    """
    return f"""Analyse this detector-improvement proposal and return
a JSON object with these exact fields:

{{
  "likely_cause": "string - likely cause of the false positive/negative",
  "proposed_rule_adjustment": "string - specific change to detection rules",
  "expected_risks": ["string - potential risks or side effects"],
  "tests_to_add": ["string - suggested test cases"],
  "confidence": 0.0-1.0,
  "uncertainty": "string - what you are uncertain about"
}}

## Proposal Context

**Detector:** {proposal.detector_name} (v{proposal.detector_version})
**Warning type:** {proposal.warning_type} ({proposal.warning_severity})
**Explanation:** {proposal.warning_explanation}

**Site:** {proposal.site_name} ({proposal.site_url})
**Page type:** {proposal.site_page_type}

**Expected signals:**
{chr(10).join(f"- {s}" for s in proposal.expected_signals) or "- (none)"}

**Observed issue IDs:**
{chr(10).join(f"- {i}" for i in proposal.observed_issue_ids) or "- (none)"}

**Evidence:**
{chr(10).join(f"- {k}: {v}" for k, v in proposal.evidence.items()) or "- (none)"}

**Signal summary:**
{
        chr(10).join(
            f"- {k}: {v}" for k, v in proposal.signal_summary.items() if v and v != 0
        )
        or "- (none)"
    }

**Text excerpts (sanitised):**
{chr(10).join(f"> {e}" for e in proposal.text_excerpts) or "> (none)"}

**Related tests:**
{chr(10).join(f"- {t}" for t in proposal.related_tests) or "- (none)"}

Return ONLY the JSON object, no other text."""


# ---------------------------------------------------------------------------
# Suggestion parsing
# ---------------------------------------------------------------------------


def parse_suggestion(raw_response: str) -> DetectorSuggestion:
    """Parse an LLM response into a DetectorSuggestion.

    Attempts to extract JSON from the response, handling common
    formatting issues (markdown fences, extra text).
    """
    text = raw_response.strip()

    # Try to extract JSON from markdown code fences
    if "```json" in text:
        start = text.index("```json") + 7
        end = text.index("```", start)
        text = text[start:end].strip()
    elif "```" in text:
        start = text.index("```") + 3
        end = text.index("```", start)
        text = text[start:end].strip()

    # Try to find JSON object in the text
    if not text.startswith("{"):
        start = text.find("{")
        end = text.rfind("}") + 1
        if start >= 0 and end > start:
            text = text[start:end]

    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise LLMProviderError(f"Failed to parse LLM response as JSON: {exc}") from exc

    return DetectorSuggestion(**data)
