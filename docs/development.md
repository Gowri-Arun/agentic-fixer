# Development Guide

## Backend Checks

```bash
ruff check backend
ruff format --check backend
pytest
```

## Frontend Checks

```bash
cd frontend
npm run build
```

## All Checks

```bash
make check
```

## Branching

Use feature branches for meaningful units of work.

```bash
git checkout main
git pull origin main
git checkout -b feature/your-feature
```

## Commit Style

Use concise conventional-style commits:

- `feat:` — New feature
- `fix:` — Bug fix
- `chore:` — Maintenance task
- `test:` — Adding or updating tests
- `docs:` — Documentation changes
- `style:` — Code style changes (formatting, etc.)

## CI

**Backend CI** runs on every push and pull request:
- Ruff lint check
- Ruff format check
- pytest

**Frontend CI** runs on every push and pull request:
- TypeScript build
- Vite production build

**Real-Site Evaluation** runs weekly (Monday 06:00 UTC) and on manual dispatch:
- Installs Playwright Chromium for browser fallback
- Runs the evaluation corpus with automatic HTTP → browser fallback
- Generates JSON, CSV, and Markdown reports
- Compares against the previous run when available
- Uploads all artifacts with 90-day retention

To trigger manually:
1. Go to Actions → Real-Site Evaluation
2. Click "Run workflow"
3. Choose render mode (`auto` for browser fallback, `html-only` for HTTP only)
4. Optionally limit sites or adjust concurrency

To run locally:
```bash
cd backend
pip install -r requirements.txt
playwright install chromium --with-deps
python -m scripts.evaluate_sites --render-mode auto -v
```

### Smoke Evaluation (Pull Requests)

**Smoke Evaluation** runs on pull requests when backend paths change
(detectors, parser, fetchers, scoring, evaluation). It uses a small
corpus of 5 stable sites (`evaluation/smoke.yml`) and applies tolerant
regression rules:

- **Does not fail** for isolated timeouts, 403s, or external-site changes
- **Fails** for response-schema breakage (missing required fields)
- **Fails** for catastrophic runner failures (unhandled exceptions)
- **Fails** when too many previously-working sites crash
- **Fails** for significant increases in validation warnings

Unit tests remain the primary mandatory gate. Smoke evaluation is
advisory — it reports regressions via artifacts and annotations but does
not block merging.

To run locally:
```bash
cd backend
python -m scripts.smoke_evaluate -v
```

### Scheduled vs Smoke Evaluation

| Aspect | Smoke (PR) | Scheduled (Weekly) |
|--------|-----------|-------------------|
| Trigger | PR (path-filtered) | Weekly + manual |
| Corpus | 5 stable sites | Full 25-site corpus |
| Timeout | 15 minutes | 60 minutes |
| Regression rules | Tolerant | Standard |
| Blocks merge | No (advisory) | No |
| Artifacts | 30-day retention | 90-day retention |

## Project Structure

```
backend/
├── app/
│   ├── main.py           FastAPI application
│   ├── schemas.py         Pydantic models
│   ├── fetcher.py         HTML fetching
│   ├── parser.py          HTML parsing
│   ├── scoring.py         Score calculation
│   ├── demo_pages.py      Demo example management
│   ├── detectors/         Detection rules
│   ├── fixes/             Fix generation
│   └── reporting/         Grade, summary, metadata
├── sample_pages/          Demo HTML files
├── tests/                 Backend tests
└── requirements.txt       Python dependencies

frontend/
├── src/
│   ├── App.tsx            Main component
│   ├── api/               API client
│   ├── types/             TypeScript types
│   ├── components/        React components
│   └── utils/             Utility functions
├── package.json           Node dependencies
└── vite.config.ts         Vite configuration

docs/                      Project documentation
.github/workflows/         CI workflows
```

## Running Locally

### Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

## Adding a New Detector

1. Create a new file in `backend/app/detectors/`
2. Implement the detection logic
3. Register the detector in `backend/app/detectors/runner.py`
4. Add tests in `backend/tests/`

## Adding a New Fix Stack

1. Create a new file in `backend/app/fixes/`
2. Implement fix templates for each issue type
3. Register the stack in `backend/app/fixes/registry.py`
4. Add tests in `backend/tests/`
