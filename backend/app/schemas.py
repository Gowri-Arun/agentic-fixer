from typing import Literal

from pydantic import BaseModel, HttpUrl

TargetStack = Literal["nextjs-13", "react-spa", "plain-html"]
Severity = Literal["low", "medium", "high"]


class AnalyzeRequest(BaseModel):
    url: HttpUrl
    target_stack: TargetStack


class Issue(BaseModel):
    id: str
    severity: Severity
    location: str
    description: str


class Fix(BaseModel):
    issue_id: str
    title: str
    why_it_matters: str
    code_snippet: str
    instructions: list[str]


class AnalyzeResponse(BaseModel):
    score: int
    issues: list[Issue]
    fixes: list[Fix]
