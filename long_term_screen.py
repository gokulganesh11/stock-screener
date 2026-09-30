from typing import Any, Dict, Tuple


def to_number(value: Any):
    if value is None:
        return None
    text = str(value).strip()
    if not text or text.lower() in {"none", "nan", "n/a", "na", "-", "--"}:
        return None
    text = text.replace(",", "").replace("₹", "").replace("%", "")
    try:
        return float(text)
    except (TypeError, ValueError):
        return None


STRICT_RULES = [
    ("ROE > 10%", "ROE", lambda v: v > 10),
    ("ROCE > 10%", "ROCE", lambda v: v > 10),
    ("PE < 50", "PE", lambda v: 0 < v < 50),
    ("PEG < 1.5", "PEG Ratio", lambda v: 0 <= v < 1.5),
    ("Debt/Equity < 1", "Debt to Equity", lambda v: v < 1),
    ("EPS > 10", "EPS", lambda v: v > 10),
    ("Promoter > 50%", "Promoter Holding", lambda v: v > 50),
    ("Pledged < 10%", "Pledged Percentage", lambda v: v < 10),
    ("Sales growth 5Y > 10%", "Sales Growth 5Y", lambda v: v > 10),
    ("Profit growth 5Y > 10%", "Profit Growth 5Y", lambda v: v > 10),
    ("Sales growth 3Y > 10%", "Sales Growth 3Y", lambda v: v > 10),
    ("Profit growth 3Y > 10%", "Profit Growth 3Y", lambda v: v > 10),
    ("Sales latest > preceding year", "Sales Latest Year vs Preceding", lambda v: v > 0),
    ("Net profit latest > preceding year", "Profit Latest Year vs Preceding", lambda v: v > 0),
    ("Sales latest quarter > 0", "Sales Latest Quarter", lambda v: v > 0),
    ("Net profit latest quarter > 0", "Net Profit Latest Quarter", lambda v: v > 0),
]


def evaluate_strict_screen(data: Dict[str, Any]) -> Dict[str, Any]:
    passed, failed, unavailable = [], [], []
    for label, key, predicate in STRICT_RULES:
        value = to_number(data.get(key))
        if value is None:
            unavailable.append(label)
        elif predicate(value):
            passed.append(label)
        else:
            failed.append(label)
    return {
        "strict_pass": len(passed) == len(STRICT_RULES),
        "passed_count": len(passed),
        "total_count": len(STRICT_RULES),
        "failed": failed,
        "unavailable": unavailable,
        "failed_or_unverified": failed + [f"{x} (unverified)" for x in unavailable],
    }


def _positive(v):
    return v is not None and v > 0


def long_term_score(data: Dict[str, Any]) -> Tuple[int, Dict[str, int]]:
    """Research score, not a return forecast.

    The score rewards durable profitability, multi-year growth, sensible leverage,
    reasonable valuation, ownership alignment, consistency and cash generation.
    It is intentionally separate from the strict screen.
    """
    parts = {
        "Quality": 0,
        "Growth": 0,
        "Balance Sheet": 0,
        "Valuation": 0,
        "Ownership": 0,
        "Consistency": 0,
        "Cash Flow": 0,
    }
    roe, roce = to_number(data.get("ROE")), to_number(data.get("ROCE"))
    if roe is not None:
        parts["Quality"] += 8 if roe >= 20 else 5 if roe > 10 else 0
    if roce is not None:
        parts["Quality"] += 8 if roce >= 20 else 5 if roce > 10 else 0

    for key in ("Sales Growth 3Y", "Sales Growth 5Y", "Profit Growth 3Y", "Profit Growth 5Y"):
        v = to_number(data.get(key))
        if v is not None:
            parts["Growth"] += 6 if v >= 20 else 4 if v > 10 else 0

    debt = to_number(data.get("Debt to Equity"))
    if debt is not None:
        parts["Balance Sheet"] += 10 if debt < 0.5 else 6 if debt < 1 else 0

    pe, peg = to_number(data.get("PE")), to_number(data.get("PEG Ratio"))
    if pe is not None and pe > 0:
        parts["Valuation"] += 6 if pe < 25 else 3 if pe < 50 else 0
    if peg is not None and peg >= 0:
        parts["Valuation"] += 6 if peg < 1 else 3 if peg < 1.5 else 0

    promoter, pledged = to_number(data.get("Promoter Holding")), to_number(data.get("Pledged Percentage"))
    if promoter is not None:
        parts["Ownership"] += 5 if promoter > 60 else 3 if promoter > 50 else 0
    if pledged is not None:
        parts["Ownership"] += 5 if pledged < 1 else 3 if pledged < 10 else 0

    if _positive(to_number(data.get("Sales Latest Year vs Preceding"))):
        parts["Consistency"] += 5
    if _positive(to_number(data.get("Profit Latest Year vs Preceding"))):
        parts["Consistency"] += 5
    if _positive(to_number(data.get("Sales Latest Quarter"))):
        parts["Consistency"] += 2
    if _positive(to_number(data.get("Net Profit Latest Quarter"))):
        parts["Consistency"] += 3

    if _positive(to_number(data.get("Free Cash Flow"))):
        parts["Cash Flow"] += 6
    cfo = to_number(data.get("CFO/OP"))
    if cfo is not None:
        parts["Cash Flow"] += 4 if cfo >= 70 else 2 if cfo >= 50 else 0

    raw = sum(parts.values())
    max_score = 97
    return round(raw / max_score * 100), parts
