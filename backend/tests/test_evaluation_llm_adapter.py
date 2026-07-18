"""Tests for LLM adapter and proposal saver.

Uses mock-based provider interface tests to avoid real API calls.
"""

import json

import pytest
from app.evaluation.llm_adapter import (
    AnthropicProvider,
    DetectorSuggestion,
    LLMProposalResult,
    LLMProvider,
    LLMProviderError,
    OllamaProvider,
    OpenAIProvider,
    build_suggestion_prompt,
    get_provider,
    parse_suggestion,
)
from app.evaluation.proposal import DetectorProposal, ProposalDocument, ProposalGroup
from app.evaluation.proposal_saver import (
    UNTRUSTED_FOOTER,
    UNTRUSTED_HEADER,
    render_llm_proposal_json,
    render_llm_proposal_markdown,
    save_proposals,
)

# ---------------------------------------------------------------------------
# Mock provider for testing
# ---------------------------------------------------------------------------


class MockLLMProvider(LLMProvider):
    """Mock LLM provider for testing."""

    def __init__(
        self,
        response: str = "",
        available: bool = True,
        error: str | None = None,
    ):
        self._response = response
        self._available = available
        self._error = error
        self.call_count = 0
        self.last_prompt = ""

    def is_available(self) -> bool:
        return self._available

    def generate_suggestion(self, prompt: str) -> str:
        self.call_count += 1
        self.last_prompt = prompt
        if self._error:
            raise LLMProviderError(self._error)
        return self._response


# ---------------------------------------------------------------------------
# Test fixtures
# ---------------------------------------------------------------------------


def _make_proposal(
    detector_name: str = "pricing_detector",
    site_name: str = "Example Pricing",
) -> DetectorProposal:
    """Create a minimal DetectorProposal for testing."""
    return DetectorProposal(
        detector_name=detector_name,
        detector_version="1.0.0",
        warning_type="possible_false_negative",
        warning_severity="medium",
        warning_explanation="Pricing content detected but no issue raised.",
        related_issue_id="missing_product_or_service_schema",
        site_name=site_name,
        site_url="https://example.com/pricing",
        site_page_type="pricing",
        expected_signals=["Should have Product/Service schema"],
        observed_issue_ids=[],
        evidence={"currency_match_count": 2},
        signal_summary={"visible_text_length": 500},
        text_excerpts=["Pricing starts at $99/month"],
        related_tests=["tests/test_pricing_detector.py"],
    )


def _make_proposal_document(
    proposals: list[DetectorProposal] | None = None,
) -> ProposalDocument:
    """Create a minimal ProposalDocument for testing."""
    if proposals is None:
        proposals = [_make_proposal()]

    groups = []
    detector_map: dict[str, list[DetectorProposal]] = {}
    for p in proposals:
        key = p.detector_name
        if key not in detector_map:
            detector_map[key] = []
        detector_map[key].append(p)

    for detector_name, group_proposals in detector_map.items():
        groups.append(
            ProposalGroup(
                detector_name=detector_name,
                detector_version=group_proposals[0].detector_version,
                proposals=group_proposals,
            )
        )

    return ProposalDocument(
        run_id="test-run-id",
        run_date="2025-01-01T00:00:00",
        total_proposals=len(proposals),
        detectors_with_proposals=[g.detector_name for g in groups],
        groups=groups,
    )


def _make_suggestion_response() -> str:
    """Create a mock LLM response with valid JSON."""
    return json.dumps(
        {
            "likely_cause": (
                "The pricing schema is missing because the page uses "
                "structured data that the detector does not recognise."
            ),
            "proposed_rule_adjustment": (
                "Add support for Offer schema type in addition to Product schema."
            ),
            "expected_risks": [
                "May increase false positives on non-pricing pages with Offer schema",
            ],
            "tests_to_add": [
                "Test with Offer schema on pricing page",
                "Test with Offer schema on non-pricing page",
            ],
            "confidence": 0.75,
            "uncertainty": ("Uncertain if all pricing pages use Offer schema"),
        }
    )


# ---------------------------------------------------------------------------
# Provider interface tests
# ---------------------------------------------------------------------------


class TestMockProvider:
    """Test the mock provider works correctly."""

    def test_mock_provider_available(self):
        provider = MockLLMProvider(available=True)
        assert provider.is_available() is True

    def test_mock_provider_unavailable(self):
        provider = MockLLMProvider(available=False)
        assert provider.is_available() is False

    def test_mock_provider_returns_response(self):
        response = _make_suggestion_response()
        provider = MockLLMProvider(response=response)

        result = provider.generate_suggestion("test prompt")

        assert result == response
        assert provider.call_count == 1
        assert provider.last_prompt == "test prompt"

    def test_mock_provider_raises_error(self):
        provider = MockLLMProvider(error="API key invalid")

        with pytest.raises(LLMProviderError, match="API key invalid"):
            provider.generate_suggestion("test prompt")


class TestProviderInterface:
    """Test the provider interface contract."""

    def test_provider_implements_interface(self):
        provider = MockLLMProvider()
        assert isinstance(provider, LLMProvider)
        assert hasattr(provider, "is_available")
        assert hasattr(provider, "generate_suggestion")

    def test_provider_is_abstract(self):
        """LLMProvider cannot be instantiated directly."""
        with pytest.raises(TypeError):
            LLMProvider()  # type: ignore


# ---------------------------------------------------------------------------
# OpenAI provider tests (mocked)
# ---------------------------------------------------------------------------


class TestOpenAIProvider:
    """Test OpenAI provider with mocked HTTP."""

    def test_not_available_without_key(self, monkeypatch):
        monkeypatch.delenv("DETECTION_LLM_API_KEY", raising=False)
        provider = OpenAIProvider(api_key="")
        assert provider.is_available() is False

    def test_available_with_key(self):
        provider = OpenAIProvider(api_key="test-key")
        assert provider.is_available() is True

    def test_custom_model(self):
        provider = OpenAIProvider(api_key="test-key", model="gpt-4")
        assert provider.model == "gpt-4"

    def test_raises_when_not_available(self):
        provider = OpenAIProvider(api_key="")

        with pytest.raises(LLMProviderError, match="not configured"):
            provider.generate_suggestion("test")


# ---------------------------------------------------------------------------
# Anthropic provider tests (mocked)
# ---------------------------------------------------------------------------


class TestAnthropicProvider:
    """Test Anthropic provider with mocked HTTP."""

    def test_not_available_without_key(self, monkeypatch):
        monkeypatch.delenv("DETECTION_LLM_API_KEY", raising=False)
        provider = AnthropicProvider(api_key="")
        assert provider.is_available() is False

    def test_available_with_key(self):
        provider = AnthropicProvider(api_key="test-key")
        assert provider.is_available() is True

    def test_raises_when_not_available(self):
        provider = AnthropicProvider(api_key="")

        with pytest.raises(LLMProviderError, match="not configured"):
            provider.generate_suggestion("test")


# ---------------------------------------------------------------------------
# Ollama provider tests
# ---------------------------------------------------------------------------


class TestOllamaProvider:
    """Test Ollama provider."""

    def test_default_model(self):
        provider = OllamaProvider()
        assert provider.model == "llama3.2"

    def test_custom_model(self):
        provider = OllamaProvider(model="custom-model")
        assert provider.model == "custom-model"


# ---------------------------------------------------------------------------
# Provider factory tests
# ---------------------------------------------------------------------------


class TestGetProvider:
    """Test provider factory."""

    def test_get_openai_provider(self):
        provider = get_provider("openai")
        assert isinstance(provider, OpenAIProvider)

    def test_get_anthropic_provider(self):
        provider = get_provider("anthropic")
        assert isinstance(provider, AnthropicProvider)

    def test_get_ollama_provider(self):
        provider = get_provider("ollama")
        assert isinstance(provider, OllamaProvider)

    def test_unknown_provider_raises(self):
        with pytest.raises(ValueError, match="Unknown provider"):
            get_provider("unknown")

    def test_default_provider(self, monkeypatch):
        monkeypatch.setenv("DETECTION_LLM_PROVIDER", "anthropic")
        provider = get_provider()
        assert isinstance(provider, AnthropicProvider)


# ---------------------------------------------------------------------------
# Prompt construction tests
# ---------------------------------------------------------------------------


class TestBuildSuggestionPrompt:
    """Test prompt construction."""

    def test_prompt_includes_detector_name(self):
        proposal = _make_proposal(detector_name="faq_detector")
        prompt = build_suggestion_prompt(proposal)

        assert "faq_detector" in prompt

    def test_prompt_includes_site_name(self):
        proposal = _make_proposal(site_name="Test Site")
        prompt = build_suggestion_prompt(proposal)

        assert "Test Site" in prompt

    def test_prompt_includes_expected_fields(self):
        proposal = _make_proposal()
        prompt = build_suggestion_prompt(proposal)

        assert "likely_cause" in prompt
        assert "proposed_rule_adjustment" in prompt
        assert "expected_risks" in prompt
        assert "tests_to_add" in prompt
        assert "confidence" in prompt
        assert "uncertainty" in prompt

    def test_prompt_includes_evidence(self):
        proposal = _make_proposal()
        prompt = build_suggestion_prompt(proposal)

        assert "currency_match_count" in prompt

    def test_prompt_includes_text_excerpts(self):
        proposal = _make_proposal()
        prompt = build_suggestion_prompt(proposal)

        assert "Pricing starts at $99/month" in prompt


# ---------------------------------------------------------------------------
# Suggestion parsing tests
# ---------------------------------------------------------------------------


class TestParseSuggestion:
    """Test LLM response parsing."""

    def test_parse_valid_json(self):
        response = _make_suggestion_response()
        suggestion = parse_suggestion(response)

        assert isinstance(suggestion, DetectorSuggestion)
        assert suggestion.confidence == 0.75
        assert len(suggestion.expected_risks) == 1
        assert len(suggestion.tests_to_add) == 2

    def test_parse_json_in_code_fences(self):
        response = f"```json\n{_make_suggestion_response()}\n```"
        suggestion = parse_suggestion(response)

        assert isinstance(suggestion, DetectorSuggestion)
        assert suggestion.confidence == 0.75

    def test_parse_json_with_surrounding_text(self):
        response = (
            f"Here is my analysis:\n\n{_make_suggestion_response()}\n\nHope this helps!"
        )
        suggestion = parse_suggestion(response)

        assert isinstance(suggestion, DetectorSuggestion)

    def test_parse_invalid_json_raises(self):
        with pytest.raises(LLMProviderError, match="Failed to parse"):
            parse_suggestion("This is not JSON at all")

    def test_parse_missing_fields_raises(self):
        from pydantic import ValidationError

        response = json.dumps({"likely_cause": "test"})
        with pytest.raises(ValidationError):
            parse_suggestion(response)


# ---------------------------------------------------------------------------
# Proposal result model tests
# ---------------------------------------------------------------------------


class TestLLMProposalResult:
    """Test LLMProposalResult model."""

    def test_create_result(self):
        suggestion = DetectorSuggestion(
            likely_cause="Test cause",
            proposed_rule_adjustment="Test adjustment",
            confidence=0.8,
            uncertainty="Test uncertainty",
        )

        result = LLMProposalResult(
            proposal_id="test_1",
            detector_name="pricing_detector",
            site_name="Test Site",
            suggestion=suggestion,
            raw_response="test",
            provider="MockProvider",
            model="test-model",
        )

        assert result.proposal_id == "test_1"
        assert result.detector_name == "pricing_detector"
        assert result.suggestion.confidence == 0.8


# ---------------------------------------------------------------------------
# Proposal saver tests
# ---------------------------------------------------------------------------


class TestRenderLLMProposalMarkdown:
    """Test Markdown rendering of LLM proposals."""

    def test_includes_untrusted_header(self):
        doc = _make_proposal_document()
        result = LLMProposalResult(
            proposal_id="test_1",
            detector_name="pricing_detector",
            site_name="Test Site",
            suggestion=DetectorSuggestion(
                likely_cause="Test",
                proposed_rule_adjustment="Test",
                confidence=0.8,
                uncertainty="Test",
            ),
        )

        md = render_llm_proposal_markdown(doc, [result])

        assert UNTRUSTED_HEADER.strip() in md
        assert "UNTRUSTED" in md

    def test_includes_untrusted_footer(self):
        doc = _make_proposal_document()
        result = LLMProposalResult(
            proposal_id="test_1",
            detector_name="pricing_detector",
            site_name="Test Site",
            suggestion=DetectorSuggestion(
                likely_cause="Test",
                proposed_rule_adjustment="Test",
                confidence=0.8,
                uncertainty="Test",
            ),
        )

        md = render_llm_proposal_markdown(doc, [result])

        assert UNTRUSTED_FOOTER.strip() in md

    def test_includes_suggestion_content(self):
        doc = _make_proposal_document()
        result = LLMProposalResult(
            proposal_id="test_1",
            detector_name="pricing_detector",
            site_name="Test Site",
            suggestion=DetectorSuggestion(
                likely_cause="Missing schema detection",
                proposed_rule_adjustment="Add Offer schema support",
                expected_risks=["May increase false positives"],
                tests_to_add=["Test with Offer schema"],
                confidence=0.85,
                uncertainty="Uncertain about edge cases",
            ),
        )

        md = render_llm_proposal_markdown(doc, [result])

        assert "Missing schema detection" in md
        assert "Add Offer schema support" in md
        assert "May increase false positives" in md
        assert "Test with Offer schema" in md
        assert "85%" in md

    def test_groups_by_detector(self):
        doc = _make_proposal_document(
            [
                _make_proposal(detector_name="faq_detector"),
                _make_proposal(detector_name="pricing_detector"),
            ]
        )

        result1 = LLMProposalResult(
            proposal_id="faq_1",
            detector_name="faq_detector",
            site_name="Test FAQ",
            suggestion=DetectorSuggestion(
                likely_cause="FAQ test",
                proposed_rule_adjustment="FAQ adjustment",
                confidence=0.7,
                uncertainty="FAQ uncertainty",
            ),
        )

        result2 = LLMProposalResult(
            proposal_id="pricing_1",
            detector_name="pricing_detector",
            site_name="Test Pricing",
            suggestion=DetectorSuggestion(
                likely_cause="Pricing test",
                proposed_rule_adjustment="Pricing adjustment",
                confidence=0.9,
                uncertainty="Pricing uncertainty",
            ),
        )

        md = render_llm_proposal_markdown(doc, [result1, result2])

        assert "## faq_detector" in md
        assert "## pricing_detector" in md


class TestRenderLLMProposalJson:
    """Test JSON rendering of LLM proposals."""

    def test_includes_untrusted_flag(self):
        doc = _make_proposal_document()
        result = LLMProposalResult(
            proposal_id="test_1",
            detector_name="pricing_detector",
            site_name="Test Site",
            suggestion=DetectorSuggestion(
                likely_cause="Test",
                proposed_rule_adjustment="Test",
                confidence=0.8,
                uncertainty="Test",
            ),
        )

        json_str = render_llm_proposal_json(doc, [result])
        data = json.loads(json_str)

        assert data["untrusted"] is True
        assert "NOT been reviewed" in data["warning"]

    def test_includes_results(self):
        doc = _make_proposal_document()
        result = LLMProposalResult(
            proposal_id="test_1",
            detector_name="pricing_detector",
            site_name="Test Site",
            suggestion=DetectorSuggestion(
                likely_cause="Test",
                proposed_rule_adjustment="Test",
                confidence=0.8,
                uncertainty="Test",
            ),
        )

        json_str = render_llm_proposal_json(doc, [result])
        data = json.loads(json_str)

        assert data["total_suggestions"] == 1
        assert len(data["results"]) == 1
        assert data["results"][0]["proposal_id"] == "test_1"


class TestSaveProposals:
    """Test proposal file saving."""

    def test_save_markdown(self, tmp_path):
        doc = _make_proposal_document()
        result = LLMProposalResult(
            proposal_id="test_1",
            detector_name="pricing_detector",
            site_name="Test Site",
            suggestion=DetectorSuggestion(
                likely_cause="Test",
                proposed_rule_adjustment="Test",
                confidence=0.8,
                uncertainty="Test",
            ),
        )

        filepath = save_proposals(doc, [result], tmp_path, format="markdown")

        assert filepath.exists()
        assert filepath.suffix == ".md"
        content = filepath.read_text()
        assert "UNTRUSTED" in content

    def test_save_json(self, tmp_path):
        doc = _make_proposal_document()
        result = LLMProposalResult(
            proposal_id="test_1",
            detector_name="pricing_detector",
            site_name="Test Site",
            suggestion=DetectorSuggestion(
                likely_cause="Test",
                proposed_rule_adjustment="Test",
                confidence=0.8,
                uncertainty="Test",
            ),
        )

        filepath = save_proposals(doc, [result], tmp_path, format="json")

        assert filepath.exists()
        assert filepath.suffix == ".json"
        data = json.loads(filepath.read_text())
        assert data["untrusted"] is True

    def test_creates_output_dir(self, tmp_path):
        doc = _make_proposal_document()
        result = LLMProposalResult(
            proposal_id="test_1",
            detector_name="pricing_detector",
            site_name="Test Site",
            suggestion=DetectorSuggestion(
                likely_cause="Test",
                proposed_rule_adjustment="Test",
                confidence=0.8,
                uncertainty="Test",
            ),
        )

        output_dir = tmp_path / "nested" / "proposals"
        filepath = save_proposals(doc, [result], output_dir)

        assert filepath.exists()
        assert output_dir.exists()


# ---------------------------------------------------------------------------
# Integration test with mock provider
# ---------------------------------------------------------------------------


class TestIntegrationWithMock:
    """Integration test using mock provider."""

    def test_full_workflow_with_mock(self):
        """Test full workflow: prompt -> mock -> parse -> render."""
        proposal = _make_proposal()
        prompt = build_suggestion_prompt(proposal)

        # Use mock provider
        response = _make_suggestion_response()
        provider = MockLLMProvider(response=response)

        raw_response = provider.generate_suggestion(prompt)
        suggestion = parse_suggestion(raw_response)

        result = LLMProposalResult(
            proposal_id="test_1",
            detector_name=proposal.detector_name,
            site_name=proposal.site_name,
            suggestion=suggestion,
            raw_response=raw_response,
            provider="MockProvider",
            model="mock-model",
        )

        doc = _make_proposal_document([proposal])
        md = render_llm_proposal_markdown(doc, [result])

        # Verify content
        assert "UNTRUSTED" in md
        assert "pricing_detector" in md
        assert "Example Pricing" in md
        assert "Missing schema detection" in md or "likely cause" in md.lower()

    def test_multiple_proposals_workflow(self):
        """Test workflow with multiple proposals."""
        proposals = [
            _make_proposal(detector_name="faq_detector", site_name="FAQ Site"),
            _make_proposal(detector_name="pricing_detector", site_name="Pricing Site"),
        ]

        doc = _make_proposal_document(proposals)
        provider = MockLLMProvider(response=_make_suggestion_response())

        results = []
        for group in doc.groups:
            for proposal in group.proposals:
                prompt = build_suggestion_prompt(proposal)
                raw = provider.generate_suggestion(prompt)
                suggestion = parse_suggestion(raw)
                results.append(
                    LLMProposalResult(
                        proposal_id=f"{group.detector_name}_1",
                        detector_name=group.detector_name,
                        site_name=proposal.site_name,
                        suggestion=suggestion,
                        raw_response=raw,
                        provider="MockProvider",
                        model="mock-model",
                    )
                )

        md = render_llm_proposal_markdown(doc, results)

        assert provider.call_count == 2
        assert "faq_detector" in md
        assert "pricing_detector" in md
