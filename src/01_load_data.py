"""
01_load_data.py
---------------
Downloads Edmonton building permits CSV (if not already present) and loads
it into a local SQLite database with correct column types and a processing_days
field pre-calculated.

Usage:
    python src/01_load_data.py

Outputs:
    data/permits.db   — SQLite database with table `permits`
"""

import os
import sqlite3
import pandas as pd

# ── Config ────────────────────────────────────────────────────────────────────
# Resolve paths relative to project root (one level up from src/)
ROOT     = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_URL = "https://data.edmonton.ca/resource/24uj-dj8v.csv?$limit=500000"
CSV_PATH = os.path.join(ROOT, "data", "permits.csv")
DB_PATH  = os.path.join(ROOT, "data", "permits.db")

DATE_COLS = ["permit_date", "issue_date", "occupancy_granted_date"]

# ── Download (skip if already present) ───────────────────────────────────────
if not os.path.exists(CSV_PATH):
    print("Downloading permits CSV …")
    import urllib.request
    urllib.request.urlretrieve(DATA_URL, CSV_PATH)
    print(f"  Saved to {CSV_PATH}")
else:
    print(f"CSV already present at {CSV_PATH}, skipping download.")

# ── Load ──────────────────────────────────────────────────────────────────────
print("Loading CSV …")
df = pd.read_csv(CSV_PATH, low_memory=False)
print(f"  Rows: {len(df):,}   Columns: {len(df.columns)}")

# Normalise column names
df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]
print("  Columns:", list(df.columns))

# ── Parse dates ───────────────────────────────────────────────────────────────
for col in DATE_COLS:
    if col in df.columns:
        df[col] = pd.to_datetime(df[col], errors="coerce")
        print(f"  Parsed {col}  —  {df[col].notna().sum():,} valid dates")

# ── Processing time ───────────────────────────────────────────────────────────
if "permit_date" in df.columns and "issue_date" in df.columns:
    df["processing_days"] = (df["issue_date"] - df["permit_date"]).dt.days
    valid = df["processing_days"].between(0, 3650)   # cap at 10 years
    df.loc[~valid, "processing_days"] = None
    print(f"  processing_days: {df['processing_days'].notna().sum():,} valid rows")
    print(f"  Median processing time: {df['processing_days'].median():.0f} days")

# ── Store dates as ISO strings for SQLite ─────────────────────────────────────
for col in DATE_COLS:
    if col in df.columns:
        df[col] = df[col].dt.strftime("%Y-%m-%d")

# ── Write to SQLite ───────────────────────────────────────────────────────────
print(f"\nWriting to {DB_PATH} …")
con = sqlite3.connect(DB_PATH)
df.to_sql("permits", con, if_exists="replace", index=False)

# Add indexes for query performance
con.execute("CREATE INDEX IF NOT EXISTS idx_job_category   ON permits(job_category)")
con.execute("CREATE INDEX IF NOT EXISTS idx_issue_date     ON permits(issue_date)")
con.execute("CREATE INDEX IF NOT EXISTS idx_permit_date    ON permits(permit_date)")
con.execute("CREATE INDEX IF NOT EXISTS idx_neighbourhood  ON permits(neighbourhood)")
con.execute("CREATE INDEX IF NOT EXISTS idx_building_type  ON permits(building_type)")
con.commit()
con.close()

print(f"Done. Database written to {DB_PATH}")