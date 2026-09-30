from score import calculate_stock_score


def test_score_is_explainable_and_bounded():
    data = {
        "ROE": "35%",
        "ROCE": "40%",
        "Sales Growth 3Y": "55%",
        "Sales Growth 5Y": "25%",
        "Profit Growth 3Y": "60%",
        "Profit Growth 5Y": "30%",
        "PE": "18",
        "Dividend Yield": "1.2%",
        "FII Holding": "12%",
        "Promoter Holding": "60%",
        "Debt to Equity": "0.3",
    }
    result = calculate_stock_score(data)
    assert 0 <= result["Total Score"] <= 21
    assert result["Confidence"] == "High"
    assert result["Data Completeness"] == 100
    assert result["Reasons"]


def test_missing_data_reduces_confidence():
    result = calculate_stock_score({"PE": "not available"})
    assert result["Total Score"] >= 0
    assert result["Confidence"] == "Low"
    assert result["Data Completeness"] == 0
    assert result["Warnings"]
