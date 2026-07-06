# Agentic Fixer

<!-- CI badges can be added after the GitHub repository URL is finalized. -->

Agentic Fixer scans web pages for agent-readiness issues and generates stack-specific developer fixes.

## Why It Exists

Modern web pages need to be understandable by humans, search engines, and AI agents. Agentic Fixer helps identify missing structured data, unclear trust/policy signals, and document structure issues, then gives developers concrete fixes they can paste directly into their codebase.

## Features

- Live URL analysis
- Deterministic demo analysis
- Agent-readiness scoring (0–100)
- Readiness grade and summary
- Stack-agnostic detection engine
- Stack-specific fix generation
- Supported stacks:
  - Next.js 13 App Router
  - React SPA
  - Plain HTML
- Markdown report output
- JSON and Markdown export
- Copyable code snippets
- Backend and frontend CI

## Supported Checks

- FAQ content without FAQPage schema
- Pricing or commercial offering content without Product/Service schema
- Commercial pages missing visible policy or trust information
- Missing or multiple H1 headings
- Heading hierarchy jumps
- Invalid JSON-LD blocks

## Tech Stack

- **Backend:** FastAPI, Pydantic, BeautifulSoup, requests
- **Frontend:** React, TypeScript, Vite
- **Tooling:** pytest, Ruff, GitHub Actions

## Project Structure

```
backend/          FastAPI backend with detection engine and fix generation
frontend/         React frontend with TypeScript
docs/             Project documentation
.github/          CI workflows
```

## Local Setup

### Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

macOS/Linux:

```bash
source .venv/bin/activate
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

## Environment Variables

Backend configuration is in:

```txt
backend/.env.example
```

Frontend configuration is in:

```txt
frontend/.env.example
```

The frontend uses:

```txt
VITE_API_BASE_URL=http://127.0.0.1:8000
```

## API Overview

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Health check |
| `/analyze` | POST | Live URL analysis |
| `/examples` | GET | List demo examples |
| `/analyze-demo` | POST | Analyze demo page |

Full API documentation: [docs/api.md](docs/api.md)

## Demo Flow

1. Start the backend server
2. Start the frontend dev server
3. Open the frontend in your browser
4. Try deterministic examples to see issues and fixes
5. Analyze a live URL if network permits
6. Copy generated fixes or export the report

Demo guide: [docs/demo.md](docs/demo.md)

## Testing and Quality

### Backend

```bash
ruff check backend
ruff format --check backend
pytest
```

### Frontend

```bash
cd frontend
npm run build
```

### All Checks

```bash
make check
```

## Current Limitations

- Detection is heuristic and rule-based
- Raw `requests` fetching may not fully capture JavaScript-rendered pages
- Generated snippets use placeholders and should be reviewed before production use
- No automatic code patching yet

## Roadmap

- JavaScript-rendered page support
- Richer schema extraction
- GitHub PR patch generation
- Browser extension
- Hosted demo

## Screenshots

Screenshots can be added under `docs/assets/` after the local demo is captured.

## License

License not specified yet.
