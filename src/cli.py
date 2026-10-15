"""Deal finder: import listings, rank them against the buyer profile, and draft outreach.

Usage:
  python -m src.cli import FILE [FILE ...]   add listings from xlsx/csv to data/listings.csv
  python -m src.cli match [--sector S] [--all]
  python -m src.cli brokers SECTOR
  python -m src.cli outreach listings [--top N]
  python -m src.cli outreach brokers [--sector S]
"""
import argparse
import csv
import json
import re
import sys
from pathlib import Path

from . import importer, matcher, outreach

ROOT = Path(__file__).resolve().parent.parent
PROFILE = ROOT / "config" / "buyer_profile.json"
LISTINGS = ROOT / "data" / "listings.csv"
BROKERS = ROOT / "data" / "brokers.csv"
OUT = ROOT / "out"


def load_profile():
    return json.loads(PROFILE.read_text())


def load_brokers():
    with BROKERS.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def cmd_import(args):
    existing = importer.load_listings(LISTINGS) if LISTINGS.exists() else []
    new = [r for path in args.files for r in importer.read_source(path)]
    rows, added, updated = importer.merge(existing, new)
    importer.write_listings(LISTINGS, rows)
    print(f"Imported {len(new)} rows: {added} new, {updated} updated. {len(rows)} total in {LISTINGS.relative_to(ROOT)}.")


def cmd_match(args):
    profile = load_profile()
    rows = importer.load_listings(LISTINGS)
    results = matcher.match(rows, profile, args.sector)
    if not args.all:
        results = [r for r in results if r["kind"] == "listing"] or results
    if not results:
        print("No matches.")
        return
    for r in results:
        rev = int(importer.parse_money(r["revenue"]) or 0)
        print(f"{r['score']:>3}  {r['name']}  [{r['kind']}]")
        print(f"     {r['sector']} | {r['location']} | revenue ${rev:,} | asking {r['asking_price'] or 'n/a'}")
        print(f"     {'; '.join(r['reasons'])}")
        if r["source"]:
            print(f"     {r['source']}")
    print(f"\n{len(results)} match(es).")


def cmd_brokers(args):
    found = matcher.brokers_for(args.sector, load_brokers())
    for b in found:
        print(f"{b['Firm']}  ({b.get('Fit for $4–10M revenue', '?')} fit for $4–10M)")
        print(f"     {b.get('Key contact(s)', '')} | {b.get('Published phone / email', '')}")
        print(f"     {b.get('Website', '')}")
    print(f"\n{len(found)} broker(s) cover {args.sector}.")


def _slug(text):
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:60]


def cmd_outreach(args):
    profile = load_profile()
    target = OUT / "outreach" / args.target
    target.mkdir(parents=True, exist_ok=True)
    count = 0
    if args.target == "listings":
        results = [r for r in matcher.match(importer.load_listings(LISTINGS), profile) if r["kind"] == "listing"]
        for r in results[: args.top]:
            subject, body = outreach.listing_email(r, profile)
            (target / f"{_slug(r['name'])}.txt").write_text(outreach.render(subject, body, r["source"]))
            count += 1
    else:
        wanted = [args.sector] if args.sector else list(profile["sectors"])
        seen = {}
        for s in wanted:
            for b in matcher.brokers_for(s, load_brokers()):
                seen.setdefault(b["Firm"], (b, []))[1].append(s)
        for b, sectors in seen.values():
            subject, body = outreach.broker_email(b, sectors, profile)
            (target / f"{_slug(b['Firm'])}.txt").write_text(outreach.render(subject, body, b.get("Published phone / email", "")))
            count += 1
    print(f"Wrote {count} draft(s) to {target.relative_to(ROOT)}/. Nothing was sent.")


def main(argv=None):
    p = argparse.ArgumentParser(prog="deal-finder", description=__doc__.split("\n")[0])
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("import", help="add listings from xlsx/csv files")
    s.add_argument("files", nargs="+")
    s.set_defaults(func=cmd_import)
    s = sub.add_parser("match", help="rank listings against the buyer profile")
    s.add_argument("--sector")
    s.add_argument("--all", action="store_true", help="include named prospects not listed for sale")
    s.set_defaults(func=cmd_match)
    s = sub.add_parser("brokers", help="brokers covering a sector")
    s.add_argument("sector")
    s.set_defaults(func=cmd_brokers)
    s = sub.add_parser("outreach", help="write draft emails")
    s.add_argument("target", choices=["listings", "brokers"])
    s.add_argument("--top", type=int, default=10)
    s.add_argument("--sector")
    s.set_defaults(func=cmd_outreach)
    args = p.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    sys.exit(main())
