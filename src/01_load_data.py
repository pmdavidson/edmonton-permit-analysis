"""
01_load_data.py
---------------
Downloads Edmonton 311 service request CSV and loads it into a local
SQLite database with correct column types and a resolution_days field
pre-calculated from date_created and date_closed.

Usage:
    python src/01_load_data.py

Outputs:
    data/requests.db   — SQLite database with table `requests`
"""

import os
import sqlite3
import pandas as pd

# ── Config ────────────────────────────────────────────────────────────────────
ROOT     = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_URL = "https://data.edmonton.ca/resource/q7ua-agfg.csv?$limit=3500000"
CSV_PATH = os.path.join(ROOT, "data", "requests.csv")
DB_PATH  = os.path.join(ROOT, "data", "requests.db")

DATE_COLS = ["date_created", "date_closed"]

# ── Download (skip if already present) ───────────────────────────────────────
if not os.path.exists(CSV_PATH):
    print("Downloading 311 requests CSV …")
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

# ── Null check on date_closed ─────────────────────────────────────────────────
closed_null_pct = df["date_closed"].isna().mean() * 100
print(f"\n  date_closed null rate: {closed_null_pct:.1f}%")
if closed_null_pct > 50:
    print("  WARNING: more than 50% of requests have no close date.")
    print("  Analysis will be limited to closed requests only.")

# ── Resolution time ───────────────────────────────────────────────────────────
df["resolution_days"] = (df["date_closed"] - df["date_created"]).dt.days
valid = df["resolution_days"].between(0, 1825)  # cap at 5 years
df.loc[~valid, "resolution_days"] = None
n_valid = df["resolution_days"].notna().sum()
print(f"  resolution_days: {n_valid:,} valid rows ({n_valid/len(df)*100:.1f}% of total)")
if n_valid > 0:
    print(f"  Median resolution time: {df['resolution_days'].median():.0f} days")

# ── Store dates as ISO strings for SQLite ─────────────────────────────────────
for col in DATE_COLS:
    if col in df.columns:
        df[col] = df[col].dt.strftime("%Y-%m-%d")

# ── Write to SQLite ───────────────────────────────────────────────────────────
print(f"\nWriting to {DB_PATH} …")
con = sqlite3.connect(DB_PATH)
df.to_sql("requests", con, if_exists="replace", index=False)

con.execute("CREATE INDEX IF NOT EXISTS idx_service_category ON requests(service_category)")
con.execute("CREATE INDEX IF NOT EXISTS idx_service_area     ON requests(service_area)")
con.execute("CREATE INDEX IF NOT EXISTS idx_neighbourhood    ON requests(neighbourhood)")
con.execute("CREATE INDEX IF NOT EXISTS idx_date_created     ON requests(date_created)")
con.execute("CREATE INDEX IF NOT EXISTS idx_request_status   ON requests(request_status)")
con.commit()
con.close()

print(f"Done. Database written to {DB_PATH}")