from urllib.parse import urlparse

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.detectors.runner import run_detectors
from app.fetcher import FetchError, fetch_html
from app.fixes.registry import generate_fixes
from app.parser import parse_html
from app.reporting.grades import get_readiness_grade
from app.reporting.markdown import generate_markdown_report
from app.reporting.metadata import build_audit_metadata
from app.reporting.summaries import generate_summary
from app.schemas import AnalyzeRequest, AnalyzeResponse
from app.scoring import calculate_score

app = FastAPI(title="Agentic Fixer")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def health_check():
    return {
        "status": "ok",
        "service": "Agentic Fixer",
    }


@app.post("/analyze", response_model=AnalyzeResponse)
def analyze_page(request: AnalyzeRequest):
    try:
        html = fetch_html(str(request.url))
    except FetchError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    parsed = parse_html(html)

    parsed_url = urlparse(str(request.url))
    location = parsed_url.path or "/"

    issues = run_detectors(parsed, location)
    score = calculate_score(issues)
    fixes = generate_fixes(issues, request.target_stack)

    grade = get_readiness_grade(score)
    summary = generate_summary(score, issues)
    metadata = build_audit_metadata(
        url=str(request.url),
        location=location,
        target_stack=request.target_stack,
        issue_count=len(issues),
        fix_count=len(fixes),
    )
    markdown_report = generate_markdown_report(
        score=score,
        grade=grade,
        summary=summary,
        issues=issues,
        fixes=fixes,
        metadata=metadata,
    )

    return AnalyzeResponse(
        score=score,
        grade=grade,
        summary=summary,
        issues=issues,
        fixes=fixes,
        metadata=metadata,
        markdown_report=markdown_report,
    )
