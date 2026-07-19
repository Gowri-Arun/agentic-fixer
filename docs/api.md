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

---

## Evaluation Endpoints

The evaluation API serves data from automated real-site evaluation runs.

### Get Latest Run

`GET /evaluation/latest`

Returns the most recent evaluation run with all site results.

**Response:**

```json
{
  "run_id": "550e8400-e29b-41d4-a716-446655440000",
  "started_at": "2025-01-15T06:00:00+00:00",
  "completed_at": "2025-01-15T06:12:34+00:00",
  "target_stack": "nextjs-13",
  "results": [
    {
      "status": "success",
      "url": "https://github.com/pricing",
      "name": "GitHub Pricing",
      "page_type": "pricing",
      "score": 75,
      "issue_ids": ["missing_product_or_service_schema"],
      "issue_count": 1,
      "duration_ms": 1234.5,
      "attempt_count": 1
    }
  ],
  "summary": {
    "total_sites": 25,
    "successful_sites": 22,
    "failed_sites": 3,
    "average_score": 72.5,
    "scores_by_page_type": {
      "pricing": 78.0,
      "faq": 65.0
    }
  }
}
```

---

### Get Run History

`GET /evaluation/history`

Returns evaluation run history sorted newest first.

**Response:**

```json
{
  "runs": [
    { "run_id": "...", "started_at": "...", "summary": {} }
  ]
}
```

---

### Get Evaluation Statistics

`GET /evaluation/stats`

Returns aggregate statistics from the latest run.

**Response:**

```json
{
  "run_id": "...",
  "total_sites": 25,
  "successful_sites": 22,
  "failed_sites": 3,
  "average_score": 72.5,
  "scores_by_page_type": { "pricing": 78.0 },
  "total_duration_ms": 45000.0,
  "success_rate": 88.0
}
```

---

### Get Regressions

`GET /evaluation/regressions`

Returns sites scoring below the median (potential regressions).

**Response:**

```json
{
  "regressions": [
    {
      "url": "https://example.com",
      "name": "Example",
      "page_type": "pricing",
      "score": 45,
      "issue_count": 3,
      "issue_ids": ["missing_faq_schema", "missing_h1"]
    }
  ],
  "threshold": 75,
  "total_sites": 25
}
```

---

### Compare Runs

`GET /evaluation/compare?baseline={run_id}&candidate={run_id}`

Compares two evaluation runs and returns per-site regression analysis.

**Classifications:**

| Classification | Condition |
|---------------|-----------|
| `blocking` | Score dropped ≥20 points with new issues |
| `warning` | Score dropped 5–19 points |
| `improved` | Score increased ≥5 points |
| `inconclusive` | Status changed or no meaningful change |

**Response:**

```json
{
  "baseline": { "run_id": "...", "started_at": "...", "git_commit": "..." },
  "candidate": { "run_id": "...", "started_at": "...", "git_commit": "..." },
  "comparisons": [
    {
      "url": "https://example.com",
      "name": "Example",
      "page_type": "pricing",
      "classification": "warning",
      "baseline_score": 80,
      "candidate_score": 70,
      "score_delta": -10,
      "issue_delta": 1,
      "reason": "Score dropped 10 points"
    }
  ]
}
```
