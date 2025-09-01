#!/usr/bin/env python3
"""
Powerball CSV updater

- Reads your local CSV (same format as NY Open Data "Lottery Powerball Winning Numbers: Beginning 2010").
- Pulls new rows via the Socrata API and appends any draws after the last date found.
- Keeps columns: Draw Date, Winning Numbers, Multiplier

Usage:
    python powerball_updater.py --csv "Lottery_Powerball_Winning_Numbers__Beginning_2010 (2).csv"
"""

import argparse, sys, os, datetime as dt
import pandas as pd
import requests

DATASET_ID = "d6yy-54nr"  # NY Open Data Powerball: Beginning 2010
BASE = "https://data.ny.gov/resource/"

def fetch_since(date_iso: str) -> pd.DataFrame:
    # Socrata uses ISO dates; query rows strictly greater than last date
    # Note: column is draw_date in the API
    params = {
        "$where": f"draw_date > '{date_iso}'",
        "$order": "draw_date asc",
        "$limit": 50000,  # plenty of headroom
    }
    url = f"{BASE}{DATASET_ID}.json"
    r = requests.get(url, params=params, timeout=30)
    r.raise_for_status()
    data = r.json()
    if not data:
        return pd.DataFrame(columns=["Draw Date","Winning Numbers","Multiplier"])
    # Normalize to our CSV columns
    recs = []
    for row in data:
        draw_date = row.get("draw_date") or row.get("drawdate") or row.get("date")
        winning_numbers = row.get("winning_numbers") or row.get("winningnumbers")
        multiplier = row.get("multiplier") or row.get("power_play") or row.get("powerplay")
        recs.append({
            "Draw Date": draw_date.split("T")[0] if draw_date else None,
            "Winning Numbers": winning_numbers,
            "Multiplier": multiplier,
        })
    df_new = pd.DataFrame(recs)
    # Ensure types
    df_new["Draw Date"] = pd.to_datetime(df_new["Draw Date"], errors="coerce").dt.date
    return df_new.sort_values("Draw Date")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", required=True, help="Path to your local CSV to update in-place")
    args = ap.parse_args()

    csv_path = args.csv
    if not os.path.exists(csv_path):
        print(f"ERROR: CSV not found: {csv_path}", file=sys.stderr)
        sys.exit(2)

    df = pd.read_csv(csv_path)
    # Be flexible with column names
    def pick(name_options):
        for n in name_options:
            if n in df.columns: return n
        # fallback to first/second/third columns if needed
        return None
    date_col = pick(["Draw Date","draw_date","Draw date","date"])
    nums_col = pick(["Winning Numbers","winning_numbers","Winning numbers"])
    mult_col = pick(["Multiplier","multiplier","Power Play","powerplay","power_play"])

    if date_col is None:
        print("ERROR: Could not find a Draw Date column in your CSV.", file=sys.stderr)
        sys.exit(3)

    df["_parsed_draw_date"] = pd.to_datetime(df[date_col], errors="coerce")
    last_date = df["_parsed_draw_date"].max()
    if pd.isna(last_date):
        # If your CSV is empty or unparsable, fetch all-time
        last_date_iso = "2009-12-31"
    else:
        last_date_iso = last_date.strftime("%Y-%m-%d")

    print(f"Last date in CSV: {last_date_iso}")
    df_new = fetch_since(last_date_iso)

    if df_new.empty:
        print("No new draws found. You're up to date!")
        return

    print(f"Appending {len(df_new)} new row(s).")
    # Conform to target columns / order
    out_cols = ["Draw Date","Winning Numbers","Multiplier"]
    # Convert dates to string for CSV consistency
    df_new["Draw Date"] = df_new["Draw Date"].astype(str)
    # Append and de-dup if needed
    if nums_col and mult_col:
        df_existing = df.rename(columns={date_col:"Draw Date", nums_col:"Winning Numbers", mult_col:"Multiplier"})
    elif nums_col and not mult_col:
        df_existing = df.rename(columns={date_col:"Draw Date", nums_col:"Winning Numbers"})
        if "Multiplier" not in df_existing.columns:
            df_existing["Multiplier"] = None
    else:
        # Minimal: only date column is present
        df_existing = df.rename(columns={date_col:"Draw Date"})
        if "Winning Numbers" not in df_existing.columns: df_existing["Winning Numbers"] = None
        if "Multiplier" not in df_existing.columns: df_existing["Multiplier"] = None

    merged = pd.concat([df_existing[out_cols], df_new[out_cols]], ignore_index=True)
    merged = merged.drop_duplicates(subset=["Draw Date"], keep="last").sort_values("Draw Date")
    merged.to_csv(csv_path, index=False)
    print(f"Updated CSV saved: {csv_path}")

if __name__ == "__main__":
    main()
