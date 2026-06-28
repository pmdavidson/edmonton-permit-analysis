"""
02_eda.py
---------
Exploratory data analysis of Edmonton 311 service request resolution times.

Produces:
  outputs/resolution_dist.png         — distribution of resolution_days
  outputs/service_category_boxplot.png — boxplot by service category
  outputs/model_ready.csv             — feature-engineered dataset for regression

Usage:
    python src/02_eda.py

Requires:
    pip install pandas matplotlib scipy
"""

import sqlite3
import os
import math
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from scipy import stats

ROOT    = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(ROOT, "data", "requests.db")
OUT_DIR = os.path.join(ROOT, "outputs")
os.makedirs(OUT_DIR, exist_ok=True)

# ── Load ──────────────────────────────────────────────────────────────────────
print("Loading from SQLite …")
con = sqlite3.connect(DB_PATH)
df  = pd.read_sql_query(
    """
    SELECT  service_category,
            service_area,
            service_description,
            interaction_channel,
            referral_type,
            neighbourhood,
            ward,
            date_created,
            date_closed,
            resolution_days,
            month_number,
            nbhd_latitude,
            nbhd_longitude
    FROM    requests
    WHERE   resolution_days >= 1
    """,
    con,
    parse_dates=["date_created", "date_closed"],
)
con.close()
print(f"  {len(df):,} closed requests with valid resolution times")

# ── Basic descriptives ────────────────────────────────────────────────────────
desc = df["resolution_days"].describe(percentiles=[.25, .5, .75, .90, .95])
print("\n── Resolution Days ──────────────────")
print(desc.round(1).to_string())

for threshold in [1, 3, 7, 30]:
    pct = (df["resolution_days"] > threshold).mean() * 100
    print(f"  % > {threshold:2d} days: {pct:.1f}%")

# ── Distribution plot ─────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(10, 5))
ax.hist(
    df["resolution_days"].clip(upper=90),
    bins=60, color="#2563EB", edgecolor="white", linewidth=0.4
)
ax.axvline(df["resolution_days"].median(), color="#DC2626", linewidth=1.5,
           linestyle="--", label=f"Median: {df['resolution_days'].median():.0f} days")
ax.set_xlabel("Resolution Days (capped at 90)")
ax.set_ylabel("Number of Requests")
ax.set_title("Distribution of 311 Request Resolution Times — Edmonton")
ax.legend()
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{int(x):,}"))
plt.tight_layout()
fig.savefig(os.path.join(OUT_DIR, "resolution_dist.png"), dpi=150)
plt.close()
print("\n  Saved: outputs/resolution_dist.png")

# ── Service category boxplot ──────────────────────────────────────────────────
top_cats = (
    df.groupby("service_category")["resolution_days"]
    .count()
    .nlargest(10)
    .index.tolist()
)
df_top = df[df["service_category"].isin(top_cats)]
order  = (
    df_top.groupby("service_category")["resolution_days"]
    .median()
    .sort_values(ascending=False)
    .index.tolist()
)

fig, ax = plt.subplots(figsize=(13, 6))
data_to_plot = [df_top[df_top["service_category"] == t]["resolution_days"].clip(upper=90)
                for t in order]
bp = ax.boxplot(data_to_plot, patch_artist=True, vert=True,
                medianprops=dict(color="#DC2626", linewidth=2))
for patch in bp["boxes"]:
    patch.set_facecolor("#BFDBFE")
ax.set_xticklabels(order, rotation=35, ha="right", fontsize=9)
ax.set_ylabel("Resolution Days (capped at 90)")
ax.set_title("Resolution Time by Service Category (Top 10 by Volume)")
plt.tight_layout()
fig.savefig(os.path.join(OUT_DIR, "service_category_boxplot.png"), dpi=150)
plt.close()
print("  Saved: outputs/service_category_boxplot.png")

# ── Seasonal pattern ──────────────────────────────────────────────────────────
monthly_avg = df.groupby("month_number")["resolution_days"].median().reset_index()
print("\n── Median Resolution Days by Month ──────────────")
print(monthly_avg.to_string(index=False))

# ── Kruskal-Wallis tests ──────────────────────────────────────────────────────
print("\n── Statistical Tests ────────────────────────────────")

for col, label in [("service_category", "service category"),
                   ("service_area",     "service area"),
                   ("interaction_channel", "interaction channel")]:
    groups = [grp["resolution_days"].values
              for _, grp in df.groupby(col) if len(grp) >= 20]
    if len(groups) >= 2:
        h, p = stats.kruskal(*groups)
        sig  = "✓ significant" if p < 0.05 else "✗ not significant"
        print(f"  Kruskal-Wallis ({label:22s}): H={h:.1f}, p={p:.4f}  — {sig}")

# ── Feature engineering ───────────────────────────────────────────────────────
print("\n── Feature Engineering ──────────────────────────────")

df["log_resolution_days"]    = df["resolution_days"].apply(lambda x: math.log1p(x))
df["service_category_enc"]   = df["service_category"].astype("category").cat.codes
df["service_area_enc"]       = df["service_area"].astype("category").cat.codes
df["interaction_channel_enc"]= df["interaction_channel"].astype("category").cat.codes
df["referral_type_enc"]      = df["referral_type"].astype("category").cat.codes
df["neighbourhood_enc"]      = df["neighbourhood"].astype("category").cat.codes

season_map = {12:"Winter",1:"Winter",2:"Winter",
              3:"Spring",4:"Spring",5:"Spring",
              6:"Summer",7:"Summer",8:"Summer",
              9:"Fall",10:"Fall",11:"Fall"}
df["season"]    = df["month_number"].map(season_map)
df["is_summer"] = df["season"].eq("Summer").astype(int)

model_cols = [
    "resolution_days", "log_resolution_days",
    "service_category_enc", "service_area_enc",
    "interaction_channel_enc", "referral_type_enc",
    "neighbourhood_enc", "month_number", "is_summer"
]
model_df = df[model_cols].dropna()
print(f"  Model-ready rows: {len(model_df):,}")
print(model_df.describe().round(2).to_string())

model_df.to_csv(os.path.join(OUT_DIR, "model_ready.csv"), index=False)
print("\n  Saved: outputs/model_ready.csv")
print("\nEDA complete.")