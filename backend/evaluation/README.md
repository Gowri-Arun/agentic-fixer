# Real-Site Evaluation Corpus

This directory contains a curated corpus of public websites for recurring evaluation of the Agentic Fixer analysis engine.

## Purpose

The `sites.yml` file provides a standardized set of real-world pages to:
- Detect regressions across detector and fix-generator changes
- Track scoring drift over time
- Ensure broad coverage of page types

## Important Caveats

1. **Live external pages** — These are real websites that can change at any time
2. **Content is not ground truth** — Website owners may update their content, affecting what issues are detected
3. **Network required** — Running evaluations requires internet access to fetch pages
4. **Disabled entries** — Some sites may be temporarily or permanently disabled due to:
   - Anti-bot measures blocking fetches
   - Content changes making the page unsuitable
   - Rate limiting concerns

## Disabling an Entry

To disable an unstable entry, set `enabled: false` in `sites.yml`:

```yaml
- name: "Unstable Site"
  url: "https://example.com/unstable"
  page_type: general
  enabled: false  # Set to false to skip during evaluation
  notes: "Disabled - blocking scrapers"
```

## Adding New Entries

When adding new sites:
1. Ensure the page is publicly accessible
2. Avoid login-only or private pages
3. Use broad expected signals (not exact issue IDs)
4. Add useful tags for categorization
5. Include brief notes if the entry has special considerations

## Category Distribution

The corpus aims for balanced coverage:
- **Pricing pages** (5+): Pages with visible pricing information
- **FAQ/Help pages** (5+): Question-answer or documentation content
- **Ecommerce pages** (5+): Product listings and shopping experiences
- **Service/General pages** (5+): SaaS products, documentation, informational content
