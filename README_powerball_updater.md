# Powerball Auto-Updater

This repo contains a small Python script that updates your local copy of the
**Lottery Powerball Winning Numbers: Beginning 2010** CSV by fetching new rows
from the New York Open Data (Socrata) API.

## Files
- `powerball_updater.py` — pulls new draws after the last date in your CSV and appends them.
- `.github/workflows/powerball_update.yml` — optional GitHub Actions workflow to auto-run daily and commit updates.

## One-time setup (local)
```bash
pip install pandas requests
python powerball_updater.py --csv "Lottery_Powerball_Winning_Numbers__Beginning_2010 (2).csv"
```

## GitHub Actions (optional)
1. Create a new, **private** GitHub repo and upload this CSV + `powerball_updater.py`.
2. Add the workflow file at `.github/workflows/powerball_update.yml`.
3. Push to GitHub. The workflow runs daily at ~09:00 Pacific and commits updates if any.

## Source
Data comes from the NY Open Data dataset `d6yy-54nr` via the Socrata API.
