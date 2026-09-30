"""Sector-aware long-term compounder research engine.

This module deliberately separates:
1) hard screening from research scoring,
2) business quality from valuation,
3) data confidence from the score.

Scores are research aids. They are not forecasts or investment advice.
"""

from __future__ import annotations

from typing import Any, Dict, Iterable, Optional, Tuple

from long_term_screen import to_number


CAPITAL_MARKET_TERMS = (
    "capital market",
    "asset management",
    "exchange and data platform",
    "financial products distributor",
    "broker",
    "stock exchange",
    "market infrastructure",
)


KEY_METRICS = (
    "ROE",
    "ROCE",
    "PE",
    "EPS",
    "Promoter Holding",
    "Pledged Percentage",
    "Sales Growth 3Y",
    "Sales Growth 5Y",
    "Profit Growth 3Y",
    "Profit Growth 5Y",
    "Sales Latest Quarter",
    "Net Profit Latest Quarter",
    "Sales Latest Year vs Preceding",
    "Profit Latest Year vs Preceding",
)


CAPITAL_MARKET_RULES = [
    ("ROE > 15%", "ROE", lambda v: v > 15),
    ("ROCE > 15%", "ROCE", lambda v: v > 15),
    ("PE < 45", "PE", lambda v: 0 < v < 45),
    ("PEG < 2.0", "PEG Ratio", lambda v: 0 <= v < 2),
    ("EPS > 0", "EPS", lambda v: v > 0),
    ("Promoter > 50%", "Promoter Holding", lambda v: v > 50),
    ("Pledged < 10%", "Pledged Percentage", lambda v: v < 10),
    ("Sales growth 5Y > 10%", "Sales Growth 5Y", lambda v: v > 10),
    ("Profit growth 5Y > 10%", "Profit Growth 5Y", lambda v: v > 10),
    ("Sales growth 3Y > 10%", "Sales Growth 3Y", lambda v: v > 10),
    ("Profit growth 3Y > 10%", "Profit Growth 3Y", lambda v: v > 10),
    ("Sales latest > preceding year", "Sales Latest Year vs Preceding", lambda v: v > 0),
    ("Profit latest > preceding year", "Profit Latest Year vs Preceding", lambda v: v > 0),
    ("Latest-quarter sales > 0", "Sales Latest Quarter", lambda v: v > 0),
    ("Latest-quarter profit > 0", "Net Profit Latest Quarter", lambda v: v > 0),
]


def is_capital_markets(industry: str | None) -> bool:
    text = str(industry or "").strip().casefold()
    return any(term in text for term in CAPITAL_MARKET_TERMS)


def _check_rules(data: Dict[str, Any], rules: Iterable[Tuple[str, str, Any]]) -> Dict[str, Any]:
    passed, failed, unavailable = [], [], []
    for label, key, predicate in rules:
        value = to_number(data.get(key))
        if value is None:
            unavailable.append(label)
        elif predicate(value):
            passed.append(label)
        else:
            failed.append(label)
    return {
        "strict_pass": len(passed) == len(list(rules)) if not isinstance(rules, list) else len(passed) == len(rules),
        "passed_count": len(passed),
        "total_count": len(rules) if isinstance(rules, list) else len(passed) + len(failed) + len(unavailable),
        "failed": failed,
        "unavailable": unavailable,
        "failed_or_unverified": failed + [f"{x} (unverified)" for x in unavailable],
    }


def evaluate_capital_markets_screen(data: Dict[str, Any]) -> Dict[str, Any]:
    """A sector-aware screen for capital-markets businesses.

    Debt/equity is intentionally not a hard condition here: balance-sheet
    leverage is not directly comparable across AMCs, exchanges and distributors.
    The app still displays debt/equity when available.
    """
    return _check_rules(data, CAPITAL_MARKET_RULES)


def _points(value: Optional[float], bands: list[tuple[float, int]], default: int = 0) -> int:
    if value is None:
        return default
    for threshold, points in bands:
        if value >= threshold:
            return points
    return 0


def _valuation_score(pe: Optional[float], peg: Optional[float]) -> int:
    score = 0
    if pe is not None and pe > 0:
        if pe <= 15:
            score += 10
        elif pe <= 20:
            score += 8
        elif pe <= 25:
            score += 6
        elif pe <= 35:
            score += 4
        elif pe < 45:
            score += 2
    if peg is not None and peg >= 0:
        if peg <= 0.75:
            score += 5
        elif peg <= 1:
            score += 4
        elif peg <= 1.5:
            score += 3
        elif peg < 2:
            score += 1
    return min(score, 15)


def _growth_score(data: Dict[str, Any]) -> int:
    sales3 = to_number(data.get("Sales Growth 3Y"))
    sales5 = to_number(data.get("Sales Growth 5Y"))
    profit3 = to_number(data.get("Profit Growth 3Y"))
    profit5 = to_number(data.get("Profit Growth 5Y"))

    score = 0
    for value in (sales5, profit5):
        score += 7 if value is not None and value >= 25 else 5 if value is not None and value >= 15 else 2 if value is not None and value > 10 else 0
    for value in (sales3, profit3):
        score += 5 if value is not None and value >= 25 else 3 if value is not None and value >= 15 else 1 if value is not None and value > 10 else 0
    return min(score, 24)


def _quality_score(data: Dict[str, Any]) -> int:
    roe = to_number(data.get("ROE"))
    roce = to_number(data.get("ROCE"))
    opm = to_number(data.get("OPM"))
    score = 0
    score += _points(roe, [(30, 12), (25, 10), (20, 8), (15, 6)])
    score += _points(roce, [(35, 12), (25, 10), (20, 8), (15, 6)])
    if opm is not None:
        score += 1 if opm >= 50 else 0
    return min(score, 25)


def _balance_and_cashflow_score(data: Dict[str, Any]) -> int:
    debt = to_number(data.get("Debt to Equity"))
    fcf = to_number(data.get("Free Cash Flow"))
    cfo = to_number(data.get("CFO/OP"))
    score = 0

    # Missing debt is neutral, not a penalty. This matters for AMCs/exchanges.
    if debt is not None:
        score += 8 if debt < 0.25 else 6 if debt < 0.5 else 4 if debt < 1 else 1 if debt < 2 else 0
    else:
        score += 4
    if fcf is not None and fcf > 0:
        score += 4
    if cfo is not None:
        score += 3 if cfo >= 80 else 2 if cfo >= 60 else 1 if cfo >= 40 else 0
    return min(score, 15)


def _ownership_score(data: Dict[str, Any]) -> int:
    promoter = to_number(data.get("Promoter Holding"))
    pledged = to_number(data.get("Pledged Percentage"))
    score = 0
    if promoter is not None:
        score += 6 if promoter >= 70 else 5 if promoter > 60 else 4 if promoter > 50 else 1
    if pledged is not None:
        score += 4 if pledged == 0 else 3 if pledged < 1 else 2 if pledged < 5 else 1 if pledged < 10 else 0
    return min(score, 10)


def _consistency_score(data: Dict[str, Any]) -> int:
    checks = [
        to_number(data.get("Sales Latest Year vs Preceding")),
        to_number(data.get("Profit Latest Year vs Preceding")),
        to_number(data.get("Sales Latest Quarter")),
        to_number(data.get("Net Profit Latest Quarter")),
    ]
    return sum(3 if value is not None and value > 0 else 0 for value in checks) + (1 if all(value is not None for value in checks) else 0)


def _data_confidence(data: Dict[str, Any]) -> int:
    available = sum(to_number(data.get(key)) is not None for key in KEY_METRICS)
    return round(available / len(KEY_METRICS) * 100)


def valuation_context(pe: Any, peer_median_pe: Any = None) -> Dict[str, Any]:
    pe_n = to_number(pe)
    median = to_number(peer_median_pe)
    if pe_n is None or pe_n <= 0:
        return {"status": "Unknown", "vs_peer_median_pct": None, "earnings_yield_pct": None}
    earnings_yield = round(100 / pe_n, 2)
    if median and median > 0:
        diff = round((pe_n / median - 1) * 100, 1)
        if pe_n <= median * 0.80:
            status = "Below peer median"
        elif pe_n <= median * 1.10:
            status = "Near peer median"
        else:
            status = "Above peer median"
        return {"status": status, "vs_peer_median_pct": diff, "earnings_yield_pct": earnings_yield}
    return {"status": "No peer median", "vs_peer_median_pct": None, "earnings_yield_pct": earnings_yield}


def compounder_score(data: Dict[str, Any], industry: str = "", peer_median_pe: Any = None) -> Dict[str, Any]:
    """Return a 100-point long-term research score plus explainable evidence."""
    quality = _quality_score(data)
    growth = _growth_score(data)
    balance = _balance_and_cashflow_score(data)
    valuation = _valuation_score(to_number(data.get("PE")), to_number(data.get("PEG Ratio")))
    ownership = _ownership_score(data)
    consistency = min(_consistency_score(data), 10)
    cash_flow = 0
    fcf = to_number(data.get("Free Cash Flow"))
    cfo = to_number(data.get("CFO/OP"))
    if fcf is not None and fcf > 0:
        cash_flow += 3
    if cfo is not None and cfo >= 70:
        cash_flow += 2

    # Balance/cash and consistency overlap slightly by design; cash conversion is
    # capped so it cannot dominate the business-quality dimensions.
    raw = quality + growth + balance + valuation + ownership + consistency + cash_flow
    score = min(100, round(raw))
    confidence = _data_confidence(data)
    valuation = valuation_context(data.get("PE"), peer_median_pe)

    red_flags = []
    for label, key, condition in [
        ("Profit growth is negative", "Profit Growth 3Y", lambda x: x is not None and x < 0),
        ("Sales growth is negative", "Sales Growth 3Y", lambda x: x is not None and x < 0),
        ("High valuation", "PE", lambda x: x is not None and x >= 45),
        ("Promoter pledge is elevated", "Pledged Percentage", lambda x: x is not None and x >= 5),
    ]:
        value = to_number(data.get(key))
        if condition(value):
            red_flags.append(label)

    if confidence < 70:
        red_flags.append("Important fields are missing; verify from filings")

    status = "Strong research candidate" if score >= 80 and confidence >= 75 else "Research candidate" if score >= 65 and confidence >= 60 else "Needs deeper verification"
    return {
        "Score": score,
        "Status": status,
        "Data Confidence": confidence,
        "Breakdown": {
            "Quality": quality,
            "Growth": growth,
            "Balance & Cash": min(balance + cash_flow, 20),
            "Valuation": valuation_score_display(to_number(data.get("PE")), to_number(data.get("PEG Ratio"))),
            "Ownership": ownership,
            "Consistency": consistency,
        },
        "Valuation": valuation,
        "Red Flags": red_flags,
        "Capital Markets Profile": is_capital_markets(industry),
    }


def valuation_score_display(pe: Optional[float], peg: Optional[float]) -> int:
    return _valuation_score(pe, peg)
