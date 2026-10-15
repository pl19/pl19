"""Score listings against the buyer profile."""
from .importer import parse_money


def detect_sectors(row, profile):
    text = " ".join(str(row.get(k, "")) for k in ("name", "sector", "notes")).lower()
    return [s for s, words in profile["sectors"].items() if any(w in text for w in words)]


def evaluate(row, profile):
    """Return (passes, score, reasons) for one listing."""
    reasons = []
    revenue = parse_money(row.get("revenue") or row.get("revenue_text"))
    sectors = detect_sectors(row, profile)
    if not sectors:
        return False, 0, ["no target sector"]
    if revenue is None:
        return False, 0, ["revenue unknown"]
    if revenue < profile["min_revenue"]:
        return False, 0, [f"revenue ${revenue:,} below minimum"]
    if profile.get("max_revenue") and revenue > profile["max_revenue"]:
        return False, 0, [f"revenue ${revenue:,} above maximum"]
    asking = parse_money(row.get("asking_price"))
    if profile.get("max_asking_price") and asking and asking > profile["max_asking_price"]:
        return False, 0, [f"asking ${asking:,} above maximum"]

    score = 50
    reasons.append("sectors: " + ", ".join(sectors))
    if str(row.get("listed", "")).lower().startswith("y") or row.get("kind") == "listing":
        score += 20
        reasons.append("actively for sale")
    if "estimate" not in str(row.get("revenue_basis", "")).lower():
        score += 10
        reasons.append("revenue reported, not estimated")
    cash_flow = parse_money(row.get("cash_flow"))
    if cash_flow and asking:
        multiple = asking / cash_flow
        reasons.append(f"asking {multiple:.1f}x cash flow")
        if multiple <= 3.5:
            score += 15
        elif multiple <= 5:
            score += 5
    notes = str(row.get("notes", "")).lower()
    for phrase, pts in (("seller financ", 5), ("management will stay", 5), ("retire", 3)):
        if phrase in notes:
            score += pts
            reasons.append(phrase)
    return True, min(score, 100), reasons


def match(rows, profile, sector=None):
    """Return matching rows sorted best first, each with score and reasons attached."""
    results = []
    for row in rows:
        ok, score, reasons = evaluate(row, profile)
        if not ok:
            continue
        if sector and sector.lower() not in " ".join(detect_sectors(row, profile)).lower():
            continue
        results.append({**row, "score": score, "reasons": reasons})
    return sorted(results, key=lambda r: r["score"], reverse=True)


def brokers_for(sector, brokers):
    """Brokers whose sector columns are ticked for the given sector."""
    out = []
    for b in brokers:
        cols = [k for k, v in b.items() if v and v.strip() == "✓"]
        matched = b.get("Sectors matched", "")
        if any(sector.lower() in c.lower() for c in cols) or sector.lower() in matched.lower():
            out.append(b)
    return out
