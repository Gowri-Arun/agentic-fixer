# Detection Rules

Agentic Fixer uses a set of heuristic detectors to identify agent-readiness issues in web pages.

## FAQ Without FAQPage Schema

**Trigger:**
- FAQ-like text or headings are detected (e.g., "Frequently Asked Questions", "FAQ")
- No `FAQPage` JSON-LD exists

**Issue:**
- ID: `missing_faq_schema`
- Severity: high
- Category: structured_data

**Why it matters:**
AI agents and search engines rely on structured FAQs to answer user questions reliably.

---

## Pricing Without Product/Service Schema

**Trigger:**
- Pricing/commercial offering language is detected (e.g., "pricing", "plans", "subscribe")
- Currency pattern is detected (e.g., `$49`, `€99`, `£29`)
- No `Product` or `Service` JSON-LD exists

**Issue:**
- ID: `missing_product_or_service_schema`
- Severity: high
- Category: structured_data

**Why it matters:**
Structured product data helps agents understand what is being offered and how to describe it.

---

## Missing Policy Surface

**Trigger:**
- Commercial intent is detected (pricing, checkout, plans)
- No visible policy/trust keywords are found (e.g., "privacy", "terms", "refund", "returns")

**Issue:**
- ID: `missing_policy_surface`
- Severity: medium
- Category: commercial_trust

**Why it matters:**
Users and agents need clear access to refund, returns, privacy, and terms information to build trust.

---

## Missing H1

**Trigger:**
- No `<h1>` heading is found in the page

**Issue:**
- ID: `missing_h1`
- Severity: medium
- Category: document_structure

**Why it matters:**
A single H1 helps agents and search engines identify the main topic of the page quickly.

---

## Multiple H1

**Trigger:**
- More than one `<h1>` heading is found in the page

**Issue:**
- ID: `multiple_h1`
- Severity: medium
- Category: document_structure

**Why it matters:**
Multiple H1 tags make the main topic ambiguous for agents and search engines.

---

## Heading Hierarchy Jump

**Trigger:**
- Heading levels skip (e.g., H2 followed by H4, skipping H3)

**Issue:**
- ID: `heading_hierarchy_jump`
- Severity: low
- Category: document_structure

**Why it matters:**
Heading hierarchy jumps confuse agents that rely on document structure to understand content relationships.

---

## Invalid JSON-LD

**Trigger:**
- One or more JSON-LD blocks fail JSON parsing

**Issue:**
- ID: `invalid_json_ld`
- Severity: medium
- Category: structured_data

**Why it matters:**
Invalid JSON-LD blocks are ignored by agents and search engines, wasting the opportunity to provide structured context.

---

## Scoring

The readiness score starts at 100 and is reduced by issues:

| Severity | Score Impact |
|----------|--------------|
| high | -20 |
| medium | -12 |
| low | -6 |

The final score is clamped between 0 and 100.

## Grades

| Score Range | Grade |
|-------------|-------|
| 90–100 | Excellent |
| 75–89 | Good |
| 50–74 | Needs Work |
| 0–49 | Poor |
