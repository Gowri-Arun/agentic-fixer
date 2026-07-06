from app.schemas import Issue

SEVERITY_PENALTIES = {
    "high": 20,
    "medium": 12,
    "low": 6,
}


def calculate_score(issues: list[Issue]) -> int:
    score = 100
    for issue in issues:
        score -= SEVERITY_PENALTIES.get(issue.severity, 0)
    return max(0, score)
