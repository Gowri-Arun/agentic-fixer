from app.schemas import Fix

_FIXES: dict[str, Fix] = {
    "missing_faq_schema": Fix(
        issue_id="missing_faq_schema",
        title="Add FAQ JSON-LD schema to the page",
        why_it_matters=(
            "FAQPage structured data helps agents and search engines "
            "understand question-answer content reliably."
        ),
        code_snippet="""\
import Script from "next/script";

const faqSchema = {
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "What is your pricing model?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Replace this with the answer shown in your FAQ section."
      }
    }
  ]
};

export default function Page() {
  return (
    <>
      <Script
        id="faq-schema"
        type="application/ld+json"
        dangerouslySetInnerHTML={{
          __html: JSON.stringify(faqSchema)
        }}
      />

      {/* Existing page content */}
    </>
  );
}""",
        instructions=[
            ("Open the relevant App Router page file, such as app/pricing/page.tsx."),
            "Import Script from next/script.",
            "Paste the faqSchema object near the top of the file.",
            "Place the Script block inside the returned JSX.",
            (
                "Replace the placeholder question and answer "
                "with the visible FAQ content from the page."
            ),
        ],
    ),
    "missing_product_or_service_schema": Fix(
        issue_id="missing_product_or_service_schema",
        title="Add Product or Service JSON-LD schema to the page",
        why_it_matters=(
            "Product or Service structured data helps agents "
            "understand what is being offered and how to describe it."
        ),
        code_snippet="""\
import Script from "next/script";

const serviceSchema = {
  "@context": "https://schema.org",
  "@type": "Service",
  "name": "Your Service Name",
  "description": "Describe the service or product offered.",
  "offers": {
    "@type": "Offer",
    "price": "99",
    "priceCurrency": "USD",
    "availability": "https://schema.org/InStock"
  }
};

export default function Page() {
  return (
    <>
      <Script
        id="service-schema"
        type="application/ld+json"
        dangerouslySetInnerHTML={{
          __html: JSON.stringify(serviceSchema)
        }}
      />

      {/* Existing page content */}
    </>
  );
}""",
        instructions=[
            "Open the relevant App Router page file.",
            "Import Script from next/script.",
            ("Paste the serviceSchema object near the top of the file."),
            "Place the Script block inside the returned JSX.",
            (
                "Replace the service name, description, price, "
                "and currency with real page data."
            ),
        ],
    ),
    "missing_policy_surface": Fix(
        issue_id="missing_policy_surface",
        title="Add visible policy and trust information section",
        why_it_matters=(
            "Users and agents need clear access to refund, "
            "returns, privacy, and terms information to build trust."
        ),
        code_snippet="""\
<section aria-labelledby="policies-heading">
  <h2 id="policies-heading">Policies and Trust Information</h2>
  <ul>
    <li><a href="/privacy">Privacy Policy</a></li>
    <li><a href="/terms">Terms of Service</a></li>
    <li><a href="/refunds">Refund and Cancellation Policy</a></li>
  </ul>
</section>""",
        instructions=[
            "Open the relevant page or layout file.",
            (
                "Paste the section into your JSX near pricing, "
                "checkout, footer, or plan comparison content."
            ),
            ("Update the href values to match your actual policy page routes."),
        ],
    ),
    "missing_h1": Fix(
        issue_id="missing_h1",
        title="Add a primary heading to the page",
        why_it_matters=(
            "A single H1 helps agents and search engines "
            "identify the main topic of the page quickly."
        ),
        code_snippet="<h1>Your clear page title goes here</h1>",
        instructions=[
            "Open the relevant page component file.",
            ("Add an H1 heading as the first visible heading in the returned JSX."),
            ("Use a concise, descriptive title that reflects the page content."),
        ],
    ),
    "multiple_h1": Fix(
        issue_id="multiple_h1",
        title="Consolidate headings into a single H1",
        why_it_matters=(
            "Multiple H1 tags make the main topic ambiguous "
            "for agents and search engines."
        ),
        code_snippet="""\
<h1>Main page title</h1>
<h2>Secondary section title</h2>""",
        instructions=[
            "Open the relevant page component file.",
            ("Keep only one H1 heading that represents the main page topic."),
            ("Convert additional H1 tags to H2 or lower heading levels."),
        ],
    ),
    "heading_hierarchy_jump": Fix(
        issue_id="heading_hierarchy_jump",
        title="Fix heading hierarchy to avoid skipped levels",
        why_it_matters=(
            "Heading hierarchy jumps confuse agents that rely "
            "on document structure to understand content relationships."
        ),
        code_snippet="""\
<h2>Section title</h2>
<h3>Subsection title</h3>""",
        instructions=[
            "Open the relevant page component file.",
            ("Ensure each heading level follows its parent without skipping."),
            ("For example, an H2 should be followed by an H3, not an H4."),
        ],
    ),
    "invalid_json_ld": Fix(
        issue_id="invalid_json_ld",
        title="Replace invalid JSON-LD with valid structured data",
        why_it_matters=(
            "Invalid JSON-LD blocks are ignored by agents and "
            "search engines, wasting the opportunity to provide "
            "structured context."
        ),
        code_snippet="""\
import Script from "next/script";

const pageSchema = {
  "@context": "https://schema.org",
  "@type": "WebPage",
  "name": "Page Title",
  "description": "Page description"
};

export default function Page() {
  return (
    <>
      <Script
        id="page-schema"
        type="application/ld+json"
        dangerouslySetInnerHTML={{
          __html: JSON.stringify(pageSchema)
        }}
      />

      {/* Existing page content */}
    </>
  );
}""",
        instructions=[
            ("Locate the invalid JSON-LD script block in your page or layout."),
            "Remove the broken script tag entirely.",
            ("Replace it with a valid JSON-LD block using next/script."),
            (
                "Validate the JSON syntax: avoid trailing commas, "
                "comments, or unquoted keys."
            ),
            ("Test the page to confirm no console errors appear."),
        ],
    ),
}


def generate_nextjs_13_fix(issue_id: str) -> Fix | None:
    return _FIXES.get(issue_id)
