# Agentic Fixer

**Agentic Fixer** is a small FastAPI-based tool that scans a live web page for **agent‑readiness issues** and returns **dev‑ready, stack‑specific fixes**.

It does two things:

1. Runs **stack‑agnostic checks** on a URL to find issues that make life hard for AI agents and search (missing structured data, unclear pricing, weak headings, hidden policies).
2. Generates **pasteable code snippets** for a chosen target stack (starting with Next.js 13, React SPA, and plain HTML), plus short instructions on where to drop them.

The idea is to go beyond “here’s a report” and make it trivial for developers to move from **diagnosis** → **patch**.

---

## Why this exists

As the internet shifts from **human‑first** to **agent‑first**, content has to be understandable not just by people but by AI agents and search engines. That usually means:

- surfacing key information (pricing, policies, FAQs) clearly in the HTML,
- adding structured data (JSON‑LD) so agents can trust and reuse it,
- keeping headings and layout predictable.

Tools like Bridge AI talk about **agentic readiness** and “dev‑ready, high‑impact fixes” to bridge this gap for real sites. Agentic Fixer is a small experimental tool that focuses on a narrow slice of that problem:

> Take any URL → detect agent‑readiness issues → output concrete fixes in the stack you care about.

---

## What it does (MVP)

For the first version, Agentic Fixer focuses on:

### Detection (stack‑agnostic)

Given a URL, it fetches the HTML and looks for:

- **FAQ without FAQ schema**
  - Page has a human‑readable FAQ section
  - No `FAQPage` JSON‑LD schema present

- **Pricing without Product/Service schema**
  - Page looks like a pricing/product page (keywords + currency patterns)
  - No `Product` or `Service` JSON‑LD schema

- **Missing policy surface**
  - No visible mention of refund/returns/shipping/privacy on pages where this matters

- **Heading hierarchy issues**
  - Missing or multiple `<h1>`
  - Deep heading jumps (e.g. `h3` without a preceding `h2`)

These checks don’t assume React/Next/WordPress/Shopify; they work purely on the rendered HTML.

### Fix generation (stack‑specific)

You choose a **target stack** you want fixes in:

- `nextjs-13` – Next.js App Router (`next/script` JSON‑LD patterns)
- `react-spa` – generic React app
- `plain-html` – vanilla HTML template

For each detected issue, Agentic Fixer returns a **Fix**:

- short title
- why it matters for agents
- **code snippet** appropriate for the chosen stack
- step‑by‑step instructions on where to paste it

Example: FAQ without schema → you get a FAQ JSON‑LD block to paste into your Next.js page (or React component / HTML template), following patterns from structured data guides.

---

## High‑level flow

1. **Request**

   Send a POST request to `/analyze` with:

   ```json
   {
     "url": "https://example.com/pricing",
     "target_stack": "nextjs-13"
   }
   ```

2. **Processing**

   Agentic Fixer:

   - Downloads and parses the HTML
   - Runs the detection rules
   - Builds an **Agentic Readiness Score** (0–100) based on issues
   - Generates stack‑specific fixes

3. **Response**

   Example (simplified):

   ```json
   {
     "score": 60,
     "issues": [
       {
         "id": "missing_faq_schema",
         "severity": "high",
         "location": "/pricing",
         "description": "FAQ section detected but no FAQPage JSON-LD structured data."
       }
     ],
     "fixes": [
       {
         "issue_id": "missing_faq_schema",
         "title": "Add FAQ JSON-LD schema to your pricing page",
         "why_it_matters": "AI agents and search engines rely on structured FAQs to answer user questions reliably.",
         "code_snippet": "// Next.js 13 Script snippet with FAQ JSON-LD",
         "instructions": [
           "Open app/pricing/page.tsx (or the page with your FAQ).",
           "Import Script from 'next/script'.",
           "Paste this Script block at the top of your component."
         ]
       }
     ]
   }
   ```

---

## Tech stack

- **Backend:** FastAPI
- **Parsing:** `requests`, `beautifulsoup4`
- **Response:** JSON (meant to power a small web UI or be called directly via CLI/Postman)
- **Frontend (optional but recommended):**
  - A simple page with:
    - URL input
    - target stack dropdown
    - “Analyze” button
    - Score + issues + code snippets rendered nicely with copy buttons

---

## Data model (conceptual)

### Issue

```json
{
  "id": "missing_faq_schema",
  "severity": "high",
  "location": "/pricing",
  "description": "FAQ section detected but no FAQPage JSON-LD structured data."
}
```

### Fix

```json
{
  "issue_id": "missing_faq_schema",
  "title": "Add FAQ JSON-LD schema to your pricing page",
  "why_it_matters": "AI agents and search engines rely on structured FAQs to answer user questions reliably.",
  "code_snippet": "// stack-specific snippet",
  "instructions": [
    "Step 1 ...",
    "Step 2 ..."
  ]
}
```

### Response

```json
{
  "score": 0,
  "issues": [],
  "fixes": []
}
```

---

## Current limitations

- Detection is intentionally simple:
  - Heuristics based on headings, text patterns, and JSON‑LD scripts
- Fix generation currently supports only:
  - Next.js 13
  - React SPA
  - Plain HTML
- Generated snippets are **patch ideas**, not auto‑applied diffs:
  - You should review and adapt them to your project conventions

---
