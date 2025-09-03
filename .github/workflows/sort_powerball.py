from pathlib import Path
import sys, re
import pandas as pd

# Accept path(s) via CLI or default
FILES = [Path(p) for p in sys.argv[1:]] or [Path("data/powerball.csv")]

DATE_CANDIDATES = {"drawdate", "draw_date", "date", "drawingdate", "draw_dt", "draw"}

def norm(s: str) -> str:
    # remove non-alphanumerics & lowercase: "Draw Date" -> "drawdate"
    return re.sub(r"[^a-z0-9]", "", s.lower())

def guess_date_col(df: pd.DataFrame) -> str | None:
    # 1) name-based match (normalized)
    for c in df.columns:
        if norm(c) in DATE_CANDIDATES:
            return c
    # 2) content-based match: pick the column that converts to datetime with the most non-null values
    best_col, best_hits = None, -1
    for c in df.columns:
        s = pd.to_datetime(df[c], errors="coerce", utc=True)
        hits = s.notna().sum()
        if hits > best_hits and hits > 0:
            best_col, best_hits = c, hits
    return best_col

def sort_file(csv_path: Path):
    if not csv_path.exists():
        print(f"#skip: {csv_path} not found")
        return

    df = pd.read_csv(csv_path, dtype=str)
    col = guess_date_col(df)
    if not col:
        print(f"#skip: {csv_path} has no date-like column (headers: {list(df.columns)})")
        return

    # ✅ Parse to datetime, then format to YYYY-MM-DD (no time)
    df[col] = pd.to_datetime(df[col], errors="coerce", utc=True).dt.date.astype(str)

    # ✅ Sort newest first
    df = df.sort_values(col, ascending=False, kind="mergesort")

    # ✅ Overwrite CSV with cleaned dates
    df.to_csv(csv_path, index=False)
    print(f"#sorted: {csv_path} by {col} (desc, date only)")

def main():
    for f in FILES:
        sort_file(f)

if __name__ == "__main__":
    sys.exit(main())
