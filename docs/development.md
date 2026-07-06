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
