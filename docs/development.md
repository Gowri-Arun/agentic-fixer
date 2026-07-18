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

### Baseline Management

The evaluation system uses **baselines** to track approved regression
reference points.  A baseline is a compact JSON manifest containing
aggregate metrics and per-site outcomes — never raw HTML.

**Baseline manifest contents:**
- Run timestamp and app version (git commit hash)
- Corpus hash (SHA-256 of the YAML file) for detecting corpus changes
- Aggregate metrics (average score, success/failure counts)
- Per-site status, scores, and issue IDs

**Workflow:**

```bash
cd backend

# 1. Create a candidate baseline
python -m scripts.baseline create -v

# 2. Review the candidate
python -m scripts.baseline status

# 3. Approve it (explicit action required)
python -m scripts.baseline approve

# 4. Compare a future run against the baseline
python -m scripts.baseline compare --run output/evaluation/latest.json
```

**Safety rules:**
- Approved baselines are never overwritten automatically
- The `create` command refuses to replace an approved baseline
  without `--approve`
- CI never auto-updates the baseline
- Corpus changes are tracked separately from detector changes
  (via corpus hash vs app version)

**When to update the baseline:**
- After intentional detector improvements that change scores
- After adding or removing sites from the corpus
- After fixing bugs that were artificially lowering scores
- When external site changes cause permanent score shifts

**When NOT to update the baseline:**
- To mask regressions
- Without running the full evaluation first
- As a quick fix for failing CI

### Evaluation Data Flow

```
1. Corpus YAML (evaluation/sites.yml or smoke.yml)
   ↓
2. Runner loads sites, filters enabled
   ↓
3. Per-site analysis (concurrent, semaphore-bounded)
   ↓
4. Fetcher: HTTP first, optional browser fallback
   ↓
5. Parser extracts signals (text, headings, schemas, keywords)
   ↓
6. Detectors run, producing evidence and issues
   ↓
7. Scoring: 100 - severity penalties = final score
   ↓
8. Validation: compare signals vs expectations → warnings
   ↓
9. Results: SiteSuccess or SiteFailure per site
   ↓
10. Aggregate: summary, scores by type, durations
   ↓
11. Output: latest.json, CSV, failed_sites.json, reports
```

### Important Caveats

- **Live websites change**: Scores may shift due to external changes
  (page redesigns, content updates), not product regressions
- **Validation warnings are review signals**: They help identify
  potential issues but are not absolute ground truth
- **No auth bypass**: The system does not log in or bypass anti-bot
  controls; sites requiring authentication will fail
- **No raw HTML persisted**: Only metadata, scores, and issue IDs
  are stored; full HTML is discarded after analysis
- **External failure ≠ regression**: A site timeout, 403, or DNS
  failure does not mean the detectors regressed

### LLM Proposal Analysis (Optional)

The evaluation system includes an **optional LLM adapter** that can
analyse detector-improvement proposals and suggest rule changes.

**Important safety properties:**
- **Disabled by default** — requires explicit provider + API key
- **Never executes** generated code
- **Never edits** detector files automatically
- **Never commits** changes or opens pull requests
- **All output marked as untrusted** — requires human review

**Configuration:**

Set environment variables before running:

```bash
# Required: LLM provider and API key
export DETECTION_LLM_PROVIDER=openai    # or anthropic, ollama
export DETECTION_LLM_API_KEY=sk-...

# Optional: custom model or base URL
export DETECTION_LLM_MODEL=gpt-4o-mini
export DETECTION_LLM_BASE_URL=https://api.openai.com/v1
```

**Data sent to the LLM:**
- Detector name and version
- Warning type and explanation
- Site name, URL, and page type
- Expected signals from corpus (descriptions only)
- Observed issue IDs
- Evidence signals (key-value pairs)
- Signal summary (text length, heading count, etc.)
- Sanitised text excerpts (emails, cards, keys redacted)
- Related test file paths

**Data NOT sent:**
- Raw HTML content
- Authentication credentials
- Cookies or session data
- Personal identifiable information (redacted)
- Full page source

**Usage:**

```bash
cd backend

# Generate proposals with LLM analysis
python -m scripts.propose --llm --provider openai -v

# Save to file
python -m scripts.propose --llm --save-dir output/proposals -v

# Use JSON output
python -m scripts.propose --llm --format json --save-dir output/proposals
```

**Provider-specific notes:**

| Provider | Default Model | Notes |
|----------|--------------|-------|
| OpenAI | gpt-4o-mini | Requires `httpx` package |
| Anthropic | claude-3-haiku | Requires `httpx` package |
| Ollama | llama3.2 | Local model, no API key needed |

**Privacy implications:**
- Proposal context is sent to external API (OpenAI/Anthropic)
- Text excerpts are sanitised but may contain page structure
- No raw HTML or credentials are transmitted
- Ollama runs locally — no data leaves your machine
- Review all LLM output before applying any suggestions

## Project Structure

```
backend/
├── app/
│   ├── main.py           FastAPI application
│   ├── schemas.py         Pydantic models
│   ├── fetcher.py         HTML fetching
│   ├── fetcher_fallback.py HTTP → browser fallback
│   ├── fetcher_browser.py  Playwright browser rendering
│   ├── parser.py          HTML parsing
│   ├── scoring.py         Score calculation
│   ├── demo_pages.py      Demo example management
│   ├── detectors/         Detection rules
│   ├── fixes/             Fix generation
│   ├── reporting/         Grade, summary, metadata
│   ├── services/          Analysis orchestration
│   └── evaluation/        Evaluation runner, API, baseline, proposals
├── evaluation/
│   ├── sites.yml          Full evaluation corpus (25 sites)
│   └── smoke.yml          Smoke test corpus (5 sites)
├── scripts/
│   ├── evaluate_sites.py  Full evaluation CLI
│   ├── smoke_evaluate.py  Smoke evaluation CLI
│   ├── baseline.py        Baseline management CLI
│   └── propose.py         Proposal context + LLM CLI
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
