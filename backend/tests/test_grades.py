from app.reporting.grades import get_readiness_grade


def test_grade_100_is_excellent():
    assert get_readiness_grade(100) == "Excellent"


def test_grade_90_is_excellent():
    assert get_readiness_grade(90) == "Excellent"


def test_grade_89_is_good():
    assert get_readiness_grade(89) == "Good"


def test_grade_75_is_good():
    assert get_readiness_grade(75) == "Good"


def test_grade_74_is_needs_work():
    assert get_readiness_grade(74) == "Needs Work"


def test_grade_50_is_needs_work():
    assert get_readiness_grade(50) == "Needs Work"


def test_grade_49_is_poor():
    assert get_readiness_grade(49) == "Poor"


def test_grade_0_is_poor():
    assert get_readiness_grade(0) == "Poor"


def test_grade_above_100_clamps_to_excellent():
    assert get_readiness_grade(150) == "Excellent"


def test_grade_below_0_clamps_to_poor():
    assert get_readiness_grade(-10) == "Poor"
