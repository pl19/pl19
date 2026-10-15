"""Load deal listings from xlsx or csv files into the standard listings.csv format."""
import csv
import re
from pathlib import Path

FIELDS = [
    "name", "kind", "sector", "location", "revenue", "revenue_text", "revenue_basis",
    "cash_flow", "asking_price", "listed", "notes", "website", "source", "checked",
]

# Header aliases seen in the research workbooks, mapped to our field names.
ALIASES = {
    "name / listing title": "name", "company": "name", "name": "name",
    "sector": "sector", "location": "location",
    "revenue (usd)": "revenue_text", "est. revenue (usd)": "revenue_text", "revenue": "revenue_text",
    "revenue basis": "revenue_basis",
    "cash flow / ebitda": "cash_flow", "asking price": "asking_price",
    "listed for sale?": "listed", "status / notes": "notes", "ownership check": "notes",
    "website": "website", "source link": "source", "checked": "checked",
}

_UNITS = {"k": 1e3, "m": 1e6, "mm": 1e6, "b": 1e9}


def parse_money(text):
    """Return the low end of a dollar amount or range as an int, or None.

    "10765274" -> 10765274, "$10M-$40M" -> 10000000, "$4.5 million" -> 4500000.
    """
    if text is None:
        return None
    if isinstance(text, (int, float)):
        return int(text)
    s = str(text).lower().replace(",", "").replace("million", "m").replace("billion", "b")
    m = re.search(r"\$?\s*(\d+(?:\.\d+)?)\s*(mm|k|m|b)?", s)
    if not m:
        return None
    return int(float(m.group(1)) * _UNITS.get(m.group(2) or "", 1))


def _normalize(row, kind):
    out = {f: "" for f in FIELDS}
    for key, value in row.items():
        field = ALIASES.get(str(key or "").strip().lower())
        if field and value not in (None, ""):
            out[field] = str(value).strip() if out[field] == "" else out[field] + "; " + str(value).strip()
    out["kind"] = kind
    out["revenue"] = parse_money(out["revenue_text"]) or ""
    return out if out["name"] else None


def _kind_for(sheet_title):
    t = sheet_title.lower()
    if "listed" in t:
        return "listing"
    if "prospect" in t:
        return "prospect"
    return None


def read_source(path):
    """Yield normalized rows from an xlsx workbook (listing/prospect sheets) or a csv."""
    path = Path(path)
    if path.suffix.lower() == ".csv":
        with path.open(newline="", encoding="utf-8-sig") as f:
            for row in csv.DictReader(f):
                if "kind" in row:  # already in our format
                    norm = {k: row.get(k, "") for k in FIELDS}
                else:
                    norm = _normalize(row, "listing")
                if norm and norm["name"]:
                    yield norm
        return
    import openpyxl  # only needed for workbooks

    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    for ws in wb.worksheets:
        kind = _kind_for(ws.title)
        if not kind:
            continue
        rows = ws.iter_rows(values_only=True)
        header = next(rows, None)
        if not header:
            continue
        for values in rows:
            norm = _normalize(dict(zip(header, values)), kind)
            if norm:
                yield norm


def load_listings(path):
    with Path(path).open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def write_listings(path, rows):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)


def merge(existing, new):
    """Add new rows, replacing any existing row with the same name (case-insensitive)."""
    by_name = {r["name"].strip().lower(): r for r in existing}
    added = updated = 0
    for r in new:
        key = r["name"].strip().lower()
        if key in by_name:
            updated += 1
        else:
            added += 1
        by_name[key] = r
    return list(by_name.values()), added, updated
