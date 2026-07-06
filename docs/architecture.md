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
| `app/parser.py` | HTML parsing and text extraction |
| `app/scoring.py` | Score calculation |
| `app/demo_pages.py` | Demo example page management |
| `app/detectors/` | Detection rules engine |
| `app/fixes/` | Stack-specific fix generation |
| `app/reporting/` | Grade, summary, metadata, markdown |

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
