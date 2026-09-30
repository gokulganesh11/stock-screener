from score import evaluate_multibagger_screen


def passing_company():
    return {
        "ROE": 20, "ROCE": 22, "PE": 25, "PEG Ratio": 1.2, "Debt to Equity": 0.4,
        "EPS": 15, "Promoter Holding": 60, "Pledged Percentage": 2,
        "Sales Growth 5Y": 15, "Profit Growth 5Y": 18, "Sales Growth 3Y": 12,
        "Profit Growth 3Y": 14, "Sales Latest": 120, "Sales Previous Year": 100,
        "Net Profit Latest": 25, "Net Profit Previous Year": 20,
        "Sales Latest Quarter": 35, "Net Profit Latest Quarter": 8,
    }


def test_all_conditions_pass():
    result = evaluate_multibagger_screen(passing_company())
    assert result["Strict Screen Pass"] is True
    assert result["Screen Checks Passed"] == result["Screen Checks Total"]


def test_missing_pledge_does_not_pass():
    data = passing_company()
    data["Pledged Percentage"] = None
    result = evaluate_multibagger_screen(data)
    assert result["Strict Screen Pass"] is False
    assert "Pledged < 10%" in result["Screen Failures"]


def test_pe_boundary_fails():
    data = passing_company()
    data["PE"] = 50
    result = evaluate_multibagger_screen(data)
    assert result["Strict Screen Pass"] is False
    assert "P/E < 50" in result["Screen Failures"]
