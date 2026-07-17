from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.demo_pages import list_example_pages
from app.evaluation.api import router as evaluation_router
from app.schemas import (
    AnalyzeRequest,
    AnalyzeResponse,
    DemoAnalyzeRequest,
    ExamplePage,
)
from app.services.analysis import AnalysisError, analyze_demo, analyze_url

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

app.include_router(evaluation_router)


@app.get("/")
def health_check():
    return {
        "status": "ok",
        "service": "Agentic Fixer",
    }


@app.get("/examples", response_model=list[ExamplePage])
def get_examples():
    """List available demo example pages."""
    return list_example_pages()


@app.post("/analyze", response_model=AnalyzeResponse)
def analyze_page(request: AnalyzeRequest):
    """Analyze a live web page for agent-readiness issues."""
    try:
        return analyze_url(str(request.url), request.target_stack)
    except AnalysisError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/analyze-demo", response_model=AnalyzeResponse)
def analyze_demo_page(request: DemoAnalyzeRequest):
    """Analyze a demo example page for agent-readiness issues."""
    try:
        return analyze_demo(request.example_id, request.target_stack)
    except AnalysisError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
