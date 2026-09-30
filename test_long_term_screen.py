from score import evaluate_multibagger_screen, calculate_long_term_score


def base_data():
    return {
        "ROE": 20, "ROCE": 22, "PE": 25, "PEG Ratio": 1.2,
        "Debt to Equity": 0.4, "EPS": 20, "Promoter Holding": 60,
        "Pledged Percentage": 2, "Sales Growth 5Y": 15,
        "Profit Growth 5Y": 18, "Sales Growth 3Y": 12,
        "Profit Growth 3Y": 14, "Sales Latest": 120,
        "Sales Previous Year": 100, "Net Profit Latest": 25,
        "Net Profit Previous Year": 20, "Sales Latest Quarter": 30,
        "Net Profit Latest Quarter": 6,
    }


def test_all_required_conditions_pass():
    result = evaluate_multibagger_screen(base_data())
    assert result["Strict Screen Pass"] is True
    assert result["Screen Checks Passed"] == result["Screen Checks Total"] == 16


def test_missing_pledge_does_not_pass():
    data = base_data()
    data["Pledged Percentage"] = None
    result = evaluate_multibagger_screen(data)
    assert result["Strict Screen Pass"] is False
    assert "Pledged < 10%" in result["Screen Failures"]


def test_thresholds_are_strict():
    data = base_data()
    data["PE"] = 50
    assert evaluate_multibagger_screen(data)["Strict Screen Pass"] is False
    data = base_data()
    data["ROE"] = 10
    assert evaluate_multibagger_screen(data)["Strict Screen Pass"] is False


def test_long_term_score_rewards_quality_and_cashflow():
    data = base_data() | {
        "ROE 5Y Average": 18, "ROCE 5Y Average": 19,
        "Sales Growth 10Y": 14, "Profit Growth 10Y": 16,
        "FCF Positive Years 5Y": 5, "CFO/OP 5Y Average": 1.1,
        "Sales YoY Quarter Growth": 15, "Profit YoY Quarter Growth": 20,
    }
    score, reasons = calculate_long_term_score(data)
    assert score > 0
    assert any("free cash flow" in reason.lower() for reason in reasons)
