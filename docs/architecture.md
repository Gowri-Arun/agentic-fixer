# Architecture

## Overview

Agentic Fixer analyzes web pages for agent-readiness issues and generates stack-specific developer fixes. The system follows a pipeline architecture:

```
User Input → HTML Source → Parser → Detectors → Scoring → Fix Generator → Audit Report → Frontend Rendering
```

## Backend Flow

1. **Fetch or Load HTML**
   - Live URLs: Fetch HTML via `requests`
   - Demo pages: Load from local sample files

2. **Parse HTML**
   - Extract visible text
   - Extract headings (h1–h6)
   - Parse valid JSON-LD blocks
   - Count invalid JSON-LD blocks

3. **Run Detectors**
   - FAQ detector
   - Pricing detector
   - Policy detector
   - Heading detector
   - Structured data detector

4. **Calculate Score**
   - Start from 100
   - Subtract points for each issue by severity
   - Clamp between 0 and 100

5. **Generate Stack-Specific Fixes**
   - Map issues to fix templates
   - Generate code snippets for target stack
   - Provide step-by-step instructions

6. **Add Audit Metadata**
   - Readiness grade (Excellent/Good/Needs Work/Poor)
   - Human-readable summary
   - Audit metadata (URL, timestamps, counts)

7. **Generate Markdown Report**
   - Compile all findings into readable markdown

## Frontend Flow

1. **User Input**
   - Enter URL or select demo example
   - Choose target stack

2. **API Call**
   - Send request to backend
   - Handle loading and error states

3. **Render Results**
   - Display score and grade
   - Show detected issues
   - Show suggested fixes with copyable code
   - Display markdown report

4. **Export Actions**
   - Copy JSON
   - Download JSON
   - Copy Markdown
   - Download Markdown
   - Copy all fixes

## Module Map

### Backend

| Module | Purpose |
|--------|---------|
| `app/main.py` | FastAPI application and endpoints |
| `app/schemas.py` | Pydantic models for request/response |
| `app/fetcher.py` | HTML fetching from URLs |
| `app/fetcher_fallback.py` | HTTP → browser fallback with quality assessment |
| `app/fetcher_browser.py` | Playwright browser rendering |
| `app/parser.py` | HTML parsing and text extraction |
| `app/scoring.py` | Score calculation |
| `app/demo_pages.py` | Demo example page management |
| `app/detectors/` | Detection rules engine |
| `app/fixes/` | Stack-specific fix generation |
| `app/reporting/` | Grade, summary, metadata, markdown |
| `app/services/analysis.py` | Analysis orchestration |
| `app/evaluation/` | Evaluation runner, models, API, baseline |

### Frontend

| Module | Purpose |
|--------|---------|
| `src/App.tsx` | Main application component |
| `src/api/analyze.ts` | Backend API client |
| `src/types/audit.ts` | TypeScript type definitions |
| `src/components/` | React UI components |
| `src/utils/` | Utility functions |

## System Flow Diagram

```
User
  ↓
React Frontend
  ↓
FastAPI Backend
  ↓
Parser → Detectors → Scoring → Fix Generator → Reporting
  ↓
Audit Response
  ↓
Frontend Rendering
```

## Key Design Decisions

1. **Stack-agnostic detection**: Detection rules work on any HTML regardless of framework
2. **Stack-specific fixes**: Code snippets are tailored to the chosen target stack
3. **Deterministic demos**: Sample pages provide predictable results without network access
4. **Shared analysis logic**: Both live and demo analysis use the same pipeline
5. **Evaluation baselines**: Approved regression reference points with corpus and version tracking

## Automated Evaluation System

The evaluation system tests detectors against real websites to catch
regressions and track agent-readiness scores over time.

### Architecture

```
Corpus YAML → Runner → Per-Site Analysis → Results JSON → API / Dashboard
                      ↓
              Fetcher (HTTP or Browser)
                      ↓
              Page Quality Assessment
                      ↓
              Detector Evidence Extraction
                      ↓
              Validation Warnings
```

### URL Corpus Structure

The corpus is defined in YAML files under `backend/evaluation/`:

```yaml
sites:
  - name: "GitHub Pricing"
    url: "https://github.com/pricing"
    page_type: pricing
    expected_signals:
      - description: "Visible pricing tiers"
    tags: [saas, pricing, developer]
    enabled: true
```

Each site entry includes:
- **name**: Human-readable identifier
- **url**: Live URL to evaluate
- **page_type**: Category (pricing, faq, ecommerce, service, general)
- **expected_signals**: Broad characteristics for validation
- **tags**: Filter tags (e.g., `smoke` for PR tests)
- **enabled**: Whether to include in runs

### Batch Evaluation

The evaluation runner (`app/evaluation/runner.py`) processes sites
concurrently with configurable parallelism:

1. Load corpus YAML and filter enabled sites
2. Create bounded concurrent tasks (semaphore-limited)
3. For each site, run analysis with optional retries
4. Collect results into `SiteSuccess` or `SiteFailure`
5. Compute aggregate summary (scores, durations, success rates)

### Retry Behavior

The `RetryPolicy` implements exponential backoff with jitter:
- Configurable max attempts (default: 2 for smoke, 3 for full)
- Retries on timeout, connection, and HTTP 429/503 errors
- Does not retry DNS failures or parsing errors
- Jitter prevents thundering herd against the same site

### HTML vs Browser Rendering

The fetcher supports three render modes:

| Mode | Description | Use Case |
|------|-------------|----------|
| `html-only` | HTTP fetch only | Fast, no JS rendering |
| `auto` | HTTP first, browser fallback on low quality | Balanced |
| `js-rendered` | Browser always | SPA-heavy sites |

In `auto` mode, the system:
1. Fetches via HTTP
2. Assesses page quality (text length, script ratio, SPA detection)
3. Falls back to Playwright Chromium if quality is below threshold

### Page Quality Assessment

Before running detectors, the system assesses page quality:

- **Text richness**: Visible text length, heading count, link count
- **Script dependency**: Script-to-text ratio, SPA root detection
- **Content signals**: Currency matches, FAQ indicators, policy links

Quality grades: `empty`, `thin`, `usable`, `rich`

### Detector Evidence

Each detector returns structured evidence beyond pass/fail:
- Matched keywords and patterns
- Schema presence flags
- Signal counts (e.g., currency matches, heading levels)

Evidence is stored in `DetectorResult.issues` as structured dicts
and exposed via the evaluation API for analysis.

### Validation Warnings

The validator (`app/evaluation/validator.py`) compares corpus
expectations against detected signals:

- `possible_fetch_failure`: Known page type with no signals
- `possible_false_negative`: Signals present but no issue raised
- `possible_false_positive`: Issue raised with weak signals
- `insufficient_evidence`: Issues with minimal page content

**Validation warnings are review signals, not absolute ground truth.**
They help identify potential issues but require human judgment.

### Category Scores

Evaluation results include scores broken down by page type:
- `pricing`: Pricing page readiness
- `faq`: FAQ page readiness
- `ecommerce`: E-commerce page readiness
- `service`: Service page readiness
- `general`: General page readiness

### Evaluation API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/evaluation/latest` | GET | Most recent run |
| `/evaluation/history` | GET | Run history (newest first) |
| `/evaluation/stats` | GET | Aggregate statistics |
| `/evaluation/regressions` | GET | Sites below median score |
| `/evaluation/compare` | GET | Compare two runs |

### Baseline Comparison

Baselines track approved regression reference points:
- Compact manifest with aggregate metrics and per-site outcomes
- Corpus hash for detecting corpus changes
- App version (git commit) for detecting detector changes
- Explicit approval required — never auto-updated in CI

### CI Schedules

| Workflow | Trigger | Corpus | Timeout |
|----------|---------|--------|---------|
| Backend CI | Every push/PR | N/A | Standard |
| Frontend CI | Every push/PR | N/A | Standard |
| Smoke Eval | PR (path-filtered) | 5 sites | 15 min |
| Scheduled Eval | Weekly + manual | 25 sites | 60 min |

### Known Limitations

- **Live websites change**: Scores may shift due to external changes,
  not product regressions
- **No auth bypass**: The system does not log in or bypass anti-bot
  controls; sites requiring auth will fail
- **No raw HTML persisted**: Only metadata, scores, and issue IDs
  are stored; full HTML is discarded
- **External failure ≠ regression**: A site timeout or 403 does not
  mean the detectors regressed
- **Browser rendering optional**: Playwright must be installed for
  browser fallback; not available in all CI environments
