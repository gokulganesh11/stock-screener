"""Explainable stock scoring engine.

The score is a research heuristic, not a prediction of future returns.
All components award points only when the underlying value is present and
parseable; missing data never receives a positive score by accident.
"""


def to_number(value):
    if value is None:
        return None

    text = str(value).strip()
    if not text or text.lower() in {"nan", "none", "-", "—", "n/a", "na"}:
        return None

    try:
        return float(
            text.replace("%", "")
            .replace(",", "")
            .replace("₹", "")
            .replace("Cr.", "")
            .replace("Cr", "")
            .strip()
        )
    except (TypeError, ValueError):
        return None


def _add_reason(reasons, text):
    reasons.append(text)


def calculate_stock_score(data):
    """Return an explainable 0-25-ish stock research score.

    Categories intentionally remain compatible with the existing Streamlit UI.
    Market cap is no longer treated as valuation: smaller companies may have
    more room to grow, but size alone is not evidence that a stock is cheap.
    """
    quality_score = 0
    growth_score = 0
    valuation_score = 0
    ownership_score = 0
    risk_score = 3
    reasons = []
    warnings = []

    roe = to_number(data.get("ROE"))
    roce = to_number(data.get("ROCE"))
    sales_3y = to_number(data.get("Sales Growth 3Y"))
    sales_5y = to_number(data.get("Sales Growth 5Y"))
    profit_3y = to_number(data.get("Profit Growth 3Y"))
    profit_5y = to_number(data.get("Profit Growth 5Y"))
    fii = to_number(data.get("FII Holding"))
    promoter = to_number(data.get("Promoter Holding"))
    dividend = to_number(data.get("Dividend Yield"))
    pe = to_number(data.get("PE"))
    debt = to_number(data.get("Debt to Equity"))

    # Quality: maximum 4
    if roe is not None:
        if roe >= 30:
            quality_score += 2
            _add_reason(reasons, "ROE above 30%")
        elif roe >= 15:
            quality_score += 1

    if roce is not None:
        if roce >= 30:
            quality_score += 2
            _add_reason(reasons, "ROCE above 30%")
        elif roce >= 15:
            quality_score += 1

    # Growth: maximum 8
    if sales_3y is not None:
        if sales_3y >= 50:
            growth_score += 3
            _add_reason(reasons, "Very strong 3Y sales growth")
        elif sales_3y >= 30:
            growth_score += 2
        elif sales_3y >= 20:
            growth_score += 1

    if profit_3y is not None:
        if profit_3y >= 50:
            growth_score += 3
            _add_reason(reasons, "Very strong 3Y profit growth")
        elif profit_3y >= 30:
            growth_score += 2
        elif profit_3y >= 20:
            growth_score += 1

    if sales_5y is not None and sales_5y >= 20:
        growth_score += 1

    if profit_5y is not None and profit_5y >= 20:
        growth_score += 1

    # Valuation: maximum 4. Dividend is a small supporting signal only.
    if pe is not None and pe > 0:
        if pe <= 20:
            valuation_score += 3
            _add_reason(reasons, "P/E at or below 20")
        elif pe <= 30:
            valuation_score += 2
        elif pe <= 50:
            valuation_score += 1
        else:
            warnings.append("P/E above 50")
    else:
        warnings.append("P/E unavailable")

    if dividend is not None and dividend >= 0.50:
        valuation_score += 1

    # Ownership: maximum 2
    if fii is not None and fii >= 10:
        ownership_score += 1
        _add_reason(reasons, "FII holding at or above 10%")

    if promoter is not None and promoter >= 50:
        ownership_score += 1
    elif promoter is not None and promoter < 50:
        risk_score -= 1
        warnings.append("Promoter holding below 50%")

    # Risk: starts at 3 and can reduce to zero.
    if pe is not None and pe > 50:
        risk_score -= 1

    if debt is not None and debt > 1:
        risk_score -= 2
        warnings.append("Debt-to-equity above 1")

    risk_score = max(0, risk_score)

    total_score = (
        quality_score
        + growth_score
        + valuation_score
        + ownership_score
        + risk_score
    )

    # Data completeness helps users distinguish a genuinely low score from
    # a score produced with many unavailable metrics.
    tracked_fields = [
        roe, roce, sales_3y, sales_5y, profit_3y, profit_5y,
        fii, promoter, dividend, pe, debt
    ]
    available = sum(value is not None for value in tracked_fields)
    completeness = round(available / len(tracked_fields) * 100)

    if completeness >= 80:
        confidence = "High"
    elif completeness >= 55:
        confidence = "Medium"
    else:
        confidence = "Low"
        warnings.append("Limited source data")

    return {
        "Total Score": total_score,
        "Quality Score": quality_score,
        "Growth Score": growth_score,
        "Valuation Score": valuation_score,
        "Ownership Score": ownership_score,
        "Risk Score": risk_score,
        "Confidence": confidence,
        "Data Completeness": completeness,
        "Reasons": reasons,
        "Warnings": warnings,
    }
