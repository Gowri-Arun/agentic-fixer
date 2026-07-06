# Demo Guide

## Run Backend

```bash
cd backend
uvicorn app.main:app --reload
```

The backend will start at `http://127.0.0.1:8000`.

## Run Frontend

```bash
cd frontend
npm install
npm run dev
```

The frontend will start at `http://localhost:5173`.

## Deterministic Examples

Agentic Fixer includes four sample pages for deterministic analysis:

| Example ID | Description | Expected Issues |
|------------|-------------|-----------------|
| `faq-no-schema` | FAQ content without JSON-LD | `missing_faq_schema` |
| `saas-pricing-missing-schema` | Pricing page without Product/Service schema | `missing_product_or_service_schema`, `missing_policy_surface` |
| `good-agent-ready-page` | Page with proper structured data | None |
| `bad-heading-structure` | Page with heading hierarchy issues | `multiple_h1`, `heading_hierarchy_jump` |

## Suggested Demo Script

1. **Start the services**
   - Open two terminals
   - Run backend in one, frontend in the other

2. **Open the frontend**
   - Navigate to `http://localhost:5173`

3. **Try the good example first**
   - Click "Good agent-ready page"
   - Show the score of 100 and "No issues detected"

4. **Try the FAQ example**
   - Click "FAQ without schema"
   - Show the missing FAQ schema issue
   - Show the generated fix with JSON-LD snippet

5. **Switch target stack**
   - Change from "Next.js 13 App Router" to "Plain HTML"
   - Re-run the same example
   - Show that the generated snippet changes

6. **Copy a fix**
   - Click "Copy" on a code snippet
   - Show the "Copied" feedback

7. **Export the report**
   - Click "Copy Markdown" to copy the report
   - Click "Download JSON" to download the full analysis

8. **Analyze a live URL** (if network permits)
   - Enter a real URL
   - Select target stack
   - Click "Analyze"

## Fallback

If live URLs fail due to network or site blocking, use the deterministic demo examples. They provide predictable results without requiring external network access.
