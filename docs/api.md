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
