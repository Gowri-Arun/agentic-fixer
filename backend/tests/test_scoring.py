from app.schemas import Issue
from app.scoring import calculate_score


def test_no_issues_gives_100():
    assert calculate_score([]) == 100


def test_high_issue_subtracts_20():
    issues = [
        Issue(id="a", severity="high", category="other", location="/", description="x")
    ]
    assert calculate_score(issues) == 80


def test_medium_issue_subtracts_12():
    issues = [
        Issue(
            id="a", severity="medium", category="other", location="/", description="x"
        )
    ]
    assert calculate_score(issues) == 88


def test_low_issue_subtracts_6():
    issues = [
        Issue(id="a", severity="low", category="other", location="/", description="x")
    ]
    assert calculate_score(issues) == 94


def test_multiple_issues_subtract_correctly():
    issues = [
        Issue(id="a", severity="high", category="other", location="/", description="x"),
        Issue(
            id="b", severity="medium", category="other", location="/", description="x"
        ),
    ]
    assert calculate_score(issues) == 68


def test_score_never_goes_below_0():
    issues = [
        Issue(
            id=f"a{i}", severity="high", category="other", location="/", description="x"
        )
        for i in range(10)
    ]
    assert calculate_score(issues) == 0
