# Deal finder

Finds manufacturing businesses to acquire (packaging, food, aerospace, electronics, oil & gas, energy, medical equipment, supplements) with at least $4M in revenue, ranks them, and drafts outreach. Python 3 standard library only; `openpyxl` is needed just to import `.xlsx` files.

## Files
- `config/buyer_profile.json`: minimum revenue, sector keywords, and your outreach pitch and signature. Edit this first.
- `data/listings.csv`: businesses for sale (`kind=listing`) and named prospects not on the market (`kind=prospect`).
- `data/brokers.csv`: M&A brokers and bankers by sector, with contacts and fit for $4–10M deals.

## Commands
```
python -m src.cli import research.xlsx       # merge new listings (xlsx sheets named "Listed..." / "...prospects", or csv)
python -m src.cli match                      # ranked for-sale listings that fit the profile
python -m src.cli match --all --sector Food  # include prospects, one sector
python -m src.cli brokers Supplements        # brokers covering a sector
python -m src.cli outreach listings --top 10 # draft inquiry emails to out/outreach/listings/
python -m src.cli outreach brokers           # draft "add me to your buyer list" emails
python -m unittest discover tests
```

Scoring: 50 for fitting sector and revenue, +20 if listed for sale, +10 if revenue is reported rather than estimated, +15 if asking ≤ 3.5x cash flow (+5 if ≤ 5x), and small bonuses for seller financing, management staying, or a retiring owner. Drafts are written to files only; nothing is ever sent.
