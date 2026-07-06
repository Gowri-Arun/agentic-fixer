from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.fetcher import FetchError, fetch_html
from app.parser import parse_html
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

    parse_html(html)

    issues = []
    fixes = []
    score = calculate_score(issues)

    return AnalyzeResponse(
        score=score,
        issues=issues,
        fixes=fixes,
    )
