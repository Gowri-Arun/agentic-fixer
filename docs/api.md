# API Reference

## Health Check

`GET /`

Returns service status.

Example response:

```json
{
  "status": "ok",
  "service": "Agentic Fixer"
}
```

## Analyze Page

`POST /analyze`

Request:

```json
{
  "url": "https://example.com",
  "target_stack": "nextjs-13"
}
```

Response:

```json
{
  "score": 100,
  "issues": [],
  "fixes": []
}
```

## Supported Target Stacks

- `nextjs-13`
- `react-spa`
- `plain-html`

## List Example Pages

`GET /examples`

Returns a list of available demo example pages for deterministic analysis.

Example response:

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

## Analyze Demo Page

`POST /analyze-demo`

Analyzes a demo example page for agent-readiness issues.

Request:

```json
{
  "example_id": "faq-no-schema",
  "target_stack": "nextjs-13"
}
```

Response: Same shape as `/analyze` endpoint.

Example IDs:

- `faq-no-schema`
- `saas-pricing-missing-schema`
- `good-agent-ready-page`
- `bad-heading-structure`
