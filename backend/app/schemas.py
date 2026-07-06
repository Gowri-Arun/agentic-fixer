from typing import Literal

from pydantic import BaseModel, HttpUrl

TargetStack = Literal["nextjs-13", "react-spa", "plain-html"]
Severity = Literal["low", "medium", "high"]
FixPriority = Literal["high", "medium", "low"]


class AnalyzeRequest(BaseModel):
    url: HttpUrl
    target_stack: TargetStack


class Issue(BaseModel):
    id: str
    severity: Severity
    category: str
    location: str
    description: str


class Fix(BaseModel):
    issue_id: str
    title: str
    priority: FixPriority
    why_it_matters: str
    code_snippet: str
    instructions: list[str]


class AuditMetadata(BaseModel):
    url: str
    location: str
    target_stack: TargetStack
    checked_at: str
    issue_count: int
    fix_count: int
    detectors_run: list[str]


class AnalyzeResponse(BaseModel):
    score: int
    grade: str
    summary: str
    issues: list[Issue]
    fixes: list[Fix]
    metadata: AuditMetadata
    markdown_report: str


class ExamplePage(BaseModel):
    id: str
    title: str
    description: str
    expected_issues: list[str]


class DemoAnalyzeRequest(BaseModel):
    example_id: str
    target_stack: TargetStack
