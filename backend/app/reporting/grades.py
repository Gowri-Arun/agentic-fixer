def get_readiness_grade(score: int) -> str:
    """
    Convert a numeric score (0-100) to a readiness grade.

    Args:
        score: The readiness score (0-100)

    Returns:
        A string grade: "Excellent", "Good", "Needs Work", or "Poor"
    """
    # Clamp score to valid range
    if score > 100:
        score = 100
    if score < 0:
        score = 0

    if score >= 90:
        return "Excellent"
    elif score >= 75:
        return "Good"
    elif score >= 50:
        return "Needs Work"
    else:
        return "Poor"
