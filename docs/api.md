# API Reference

## Health Check

`GET /`

Returns service status.

**Response:**

```json
{
  "status": "ok",
  "service": "Agentic Fixer"
}
```

---

## Analyze Page

`POST /analyze`

Analyzes a live web page for agent-readiness issues.

**Request body:**

```json
{
  "url": "https://example.com",
  "target_stack": "nextjs-13"
}
```

**Fields:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `url` | string | Yes | URL to analyze |
| `target_stack` | string | Yes | Target stack for fixes |

**Supported target stacks:**

- `nextjs-13` — Next.js 13 App Router
- `react-spa` — React single-page application
- `plain-html` — Vanilla HTML

**Response:**

```json
{
  "score": 80,
  "grade": "Good",
  "summary": "This page has structured data gaps...",
  "issues": [
    {
      "id": "missing_faq_schema",
      "severity": "high",
      "category": "structured_data",
      "location": "/pricing",
      "description": "FAQ section detected but no FAQPage JSON-LD."
    }
  ],
  "fixes": [
    {
      "issue_id": "missing_faq_schema",
      "title": "Add FAQ JSON-LD schema",
      "priority": "high",
      "why_it_matters": "Helps agents understand Q&A content.",
      "code_snippet": "...",
      "instructions": ["Step 1...", "Step 2..."]
    }
  ],
  "metadata": {
    "url": "https://example.com",
    "location": "/pricing",
    "target_stack": "nextjs-13",
    "checked_at": "2025-01-01T00:00:00+00:00",
    "issue_count": 1,
    "fix_count": 1,
    "detectors_run": ["faq", "pricing", "policy", "headings", "structured_data"]
  },
  "markdown_report": "# Agentic Readiness Audit Report\n..."
}
```

---

## List Example Pages

`GET /examples`

Returns a list of available demo example pages for deterministic analysis.

**Response:**

```json
[
  {
    "id": "faq-no-schema",
    "title": "FAQ without schema",
    "description": "FAQ content is visible, but FAQPage JSON-LD is missing.",
    "expected_issues": ["missing_faq_schema"]
  }
]
```

---

## Analyze Demo Page

`POST /analyze-demo`

Analyzes a local demo page for agent-readiness issues.

**Request body:**

```json
{
  "example_id": "faq-no-schema",
  "target_stack": "nextjs-13"
}
```

**Available example IDs:**

| ID | Description |
|----|-------------|
| `faq-no-schema` | FAQ content without schema |
| `saas-pricing-missing-schema` | Pricing page without Product/Service schema |
| `good-agent-ready-page` | Page with proper structured data |
| `bad-heading-structure` | Page with heading hierarchy issues |

**Response:** Same shape as `/analyze` endpoint.

---

## Response Shape

All analysis endpoints return the same response structure:

| Field | Type | Description |
|-------|------|-------------|
| `score` | integer | Readiness score (0–100) |
| `grade` | string | Excellent, Good, Needs Work, or Poor |
| `summary` | string | Human-readable summary |
| `issues` | array | Detected issues |
| `fixes` | array | Suggested fixes |
| `metadata` | object | Audit metadata |
| `markdown_report` | string | Full markdown report |
