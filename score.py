def to_number(value):

    if not value:
        return 0

    try:

        return float(
            str(value)
            .replace("%", "")
            .replace(",", "")
            .replace("₹", "")
            .strip()
        )

    except:

        return 0


def calculate_stock_score(data):

    quality_score = 0
    growth_score = 0
    valuation_score = 0
    ownership_score = 0
    risk_score = 0

    # -----------------------------
    # ROE
    # -----------------------------

    roe = to_number(
        data["ROE"]
    )

    if roe >= 30:
        quality_score += 2

    elif roe >= 15:
        quality_score += 1

    # -----------------------------
    # ROCE
    # -----------------------------

    roce = to_number(
        data["ROCE"]
    )

    if roce >= 30:
        quality_score += 2

    elif roce >= 15:
        quality_score += 1

    # -----------------------------
    # Sales Growth 3Y
    # -----------------------------

    sales_growth_3y = to_number(
        data["Sales Growth 3Y"]
    )

    if sales_growth_3y >= 30:
        growth_score += 2

    elif sales_growth_3y >= 20:
        growth_score += 1

    # -----------------------------
    # Profit Growth 3Y
    # -----------------------------

    profit_growth_3y = to_number(
        data["Profit Growth 3Y"]
    )

    if profit_growth_3y >= 30:
        growth_score += 2

    elif profit_growth_3y >= 20:
        growth_score += 1

    # -----------------------------
    # Sales Growth 5Y
    # -----------------------------

    sales_growth_5y = to_number(
        data["Sales Growth 5Y"]
    )

    if sales_growth_5y >= 20:
        growth_score += 1

    # -----------------------------
    # Profit Growth 5Y
    # -----------------------------

    profit_growth_5y = to_number(
        data["Profit Growth 5Y"]
    )

    if profit_growth_5y >= 20:
        growth_score += 1

    # -----------------------------
    # FII Holding
    # -----------------------------

    fii_holding = to_number(
        data.get("FII Holding")
    )

    if fii_holding >= 10:
        ownership_score += 1

    # -----------------------------
    # Promoter Holding
    # -----------------------------

    promoter_holding = to_number(
        data.get("Promoter Holding")
    )

    if promoter_holding >= 50:
        ownership_score += 1

    # -----------------------------
    # Dividend Yield
    # -----------------------------

    dividend_yield = to_number(
        data.get("Dividend Yield")
    )

    if dividend_yield >= 0.50:
        valuation_score += 1

    # -----------------------------
    # PE Valuation Score
    # -----------------------------

    pe = to_number(
        data["PE"]
    )

    if pe > 0:

        if pe <= 20:
            valuation_score += 3

        elif pe <= 30:
            valuation_score += 2

        elif pe <= 50:
            valuation_score += 1

    # -----------------------------
    # Market Cap Score
    # -----------------------------

    market_cap = to_number(
        data.get("Market Cap Cr")
    )

    if market_cap > 0:

        if market_cap <= 10000:
            valuation_score += 3

        elif market_cap <= 50000:
            valuation_score += 2

        elif market_cap <= 100000:
            valuation_score += 1

    # -----------------------------
    # Multibagger Bonus
    # -----------------------------

    if sales_growth_3y >= 50:
        growth_score += 1

    if profit_growth_3y >= 50:
        growth_score += 1

    # -----------------------------
    # Risk Score
    # -----------------------------

    risk_score = 3

    if pe > 50:
        risk_score -= 1

    debt = to_number(
        data.get("Debt to Equity")
    )

    if debt > 1:
        risk_score -= 2

    if promoter_holding > 0 and promoter_holding < 50:
        risk_score -= 1

    if risk_score < 0:
        risk_score = 0

    # -----------------------------
    # Total Score
    # -----------------------------

    total_score = (
        quality_score
        + growth_score
        + valuation_score
        + ownership_score
        + risk_score
    )

    return {
        "Total Score": total_score,
        "Quality Score": quality_score,
        "Growth Score": growth_score,
        "Valuation Score": valuation_score,
        "Ownership Score": ownership_score,
        "Risk Score": risk_score
    }