"""Strict long-term screening and explainable ranking engine."""

def to_number(value):
    if value is None: return None
    text = str(value).strip()
    if not text or text.lower() in {"nan", "none", "-", "—", "n/a", "na"}: return None
    try:
        return float(text.replace("%", "").replace(",", "").replace("₹", "").replace("Cr.", "").replace("Cr", "").strip())
    except (TypeError, ValueError):
        return None

def _gt(data, key, threshold):
    value = to_number(data.get(key)); return value is not None and value > threshold

def _lt(data, key, threshold):
    value = to_number(data.get(key)); return value is not None and value < threshold

def evaluate_multibagger_screen(data):
    """Apply the user's strict long-term screen; missing data never passes."""
    sales = to_number(data.get("Sales Latest")); sales_prev = to_number(data.get("Sales Previous Year"))
    profit = to_number(data.get("Net Profit Latest")); profit_prev = to_number(data.get("Net Profit Previous Year"))
    checks = {
        "ROE > 10": _gt(data, "ROE", 10), "ROCE > 10": _gt(data, "ROCE", 10),
        "P/E < 50": _lt(data, "PE", 50), "PEG < 1.5": _lt(data, "PEG Ratio", 1.5),
        "Debt / Equity < 1": _lt(data, "Debt to Equity", 1), "EPS > 10": _gt(data, "EPS", 10),
        "Promoter > 50%": _gt(data, "Promoter Holding", 50), "Pledged < 10%": _lt(data, "Pledged Percentage", 10),
        "Sales growth 5Y > 10%": _gt(data, "Sales Growth 5Y", 10), "Profit growth 5Y > 10%": _gt(data, "Profit Growth 5Y", 10),
        "Sales growth 3Y > 10%": _gt(data, "Sales Growth 3Y", 10), "Profit growth 3Y > 10%": _gt(data, "Profit Growth 3Y", 10),
        "Sales > preceding year": sales is not None and sales_prev is not None and sales > sales_prev,
        "Net Profit > preceding year": profit is not None and profit_prev is not None and profit > profit_prev,
        "Latest quarter Sales > 0": _gt(data, "Sales Latest Quarter", 0),
        "Latest quarter Net Profit > 0": _gt(data, "Net Profit Latest Quarter", 0),
    }
    failures = [name for name, passed in checks.items() if not passed]
    return {"Strict Screen Pass": not failures, "Screen Checks Passed": sum(checks.values()), "Screen Checks Total": len(checks), "Screen Failures": failures, "Screen Pass %": round(sum(checks.values()) / len(checks) * 100)}

def calculate_long_term_score(data):
    """Research ranking for a 10-20 year horizon; not a return prediction."""
    score = 0; reasons = []
    def add(condition, points, reason):
        nonlocal score
        if condition: score += points; reasons.append(reason)
    roe, roce = to_number(data.get("ROE")), to_number(data.get("ROCE"))
    s5, p5 = to_number(data.get("Sales Growth 5Y")), to_number(data.get("Profit Growth 5Y"))
    s10, p10 = to_number(data.get("Sales Growth 10Y")), to_number(data.get("Profit Growth 10Y"))
    pe, peg, debt = to_number(data.get("PE")), to_number(data.get("PEG Ratio")), to_number(data.get("Debt to Equity"))
    promoter, pledge = to_number(data.get("Promoter Holding")), to_number(data.get("Pledged Percentage"))
    fcf, cfo = to_number(data.get("FCF Positive Years 5Y")), to_number(data.get("CFO/OP 5Y Average"))
    q_sales, q_profit = to_number(data.get("Sales YoY Quarter Growth")), to_number(data.get("Profit YoY Quarter Growth"))
    roe5, roce5 = to_number(data.get("ROE 5Y Average")), to_number(data.get("ROCE 5Y Average"))
    add(roe > 20 if roe is not None else False, 3, "ROE > 20%")
    add(roce > 20 if roce is not None else False, 3, "ROCE > 20%")
    add(s5 > 15 if s5 is not None else False, 3, "Sales growth > 15% over 5Y")
    add(p5 > 15 if p5 is not None else False, 3, "Profit growth > 15% over 5Y")
    add(s10 > 12 if s10 is not None else False, 2, "Sales growth > 12% over 10Y")
    add(p10 > 12 if p10 is not None else False, 2, "Profit growth > 12% over 10Y")
    add(roe5 > 15 if roe5 is not None else False, 2, "5Y average ROE > 15%")
    add(roce5 > 15 if roce5 is not None else False, 2, "5Y average ROCE > 15%")
    add(debt < .5 if debt is not None else False, 3, "Debt/equity < 0.5")
    add(peg < 1.5 if peg is not None else False, 3, "PEG < 1.5")
    add(0 < pe < 35 if pe is not None else False, 2, "P/E below 35")
    add(promoter > 50 if promoter is not None else False, 2, "Promoter holding > 50%")
    add(pledge < 5 if pledge is not None else False, 2, "Pledged holding < 5%")
    add(fcf >= 4 if fcf is not None else False, 3, "Positive free cash flow in at least 4 of 5 years")
    add(cfo > 0 if cfo is not None else False, 2, "Positive operating cash-flow coverage")
    add(q_sales > 10 if q_sales is not None else False, 1, "Latest quarter sales growth > 10% YoY")
    add(q_profit > 10 if q_profit is not None else False, 1, "Latest quarter profit growth > 10% YoY")
    return score, reasons

def calculate_stock_score(data):
    screen = evaluate_multibagger_screen(data); long_score, reasons = calculate_long_term_score(data)
    warnings = list(screen["Screen Failures"])
    return {"Total Score": long_score, "Quality Score": sum("ROE" in x or "ROCE" in x for x in reasons), "Growth Score": sum("growth" in x.lower() for x in reasons), "Valuation Score": sum("P/E" in x or "PEG" in x for x in reasons), "Ownership Score": sum("Promoter" in x or "Pledged" in x for x in reasons), "Risk Score": sum("Debt" in x or "cash flow" in x.lower() for x in reasons), "Confidence": "High" if screen["Screen Pass %"] >= 90 else "Medium" if screen["Screen Pass %"] >= 70 else "Low", "Data Completeness": screen["Screen Pass %"], "Reasons": reasons, "Warnings": warnings, **screen}
