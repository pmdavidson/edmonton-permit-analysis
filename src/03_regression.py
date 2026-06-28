"""
03_regression.py
----------------
OLS regression predicting 311 request resolution time using statsmodels.
Produces a full model summary (p-values, confidence intervals, R²),
a coefficient plot, and a CSV of results ready for Power BI.

Usage:
    python src/03_regression.py

Inputs:
    outputs/model_ready.csv   (produced by 02_eda.py)

Outputs:
    outputs/regression_summary.txt
    outputs/coefficient_plot.png
    outputs/model_coefficients.csv   ← import into Power BI
"""

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import statsmodels.api as sm
from statsmodels.stats.outliers_influence import variance_inflation_factor

ROOT    = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(ROOT, "outputs")
os.makedirs(OUT_DIR, exist_ok=True)

# ── Load ──────────────────────────────────────────────────────────────────────
print("Loading model-ready data …")
df = pd.read_csv(os.path.join(OUT_DIR, "model_ready.csv"))
print(f"  {len(df):,} rows")

# ── Feature matrix ────────────────────────────────────────────────────────────
feature_cols = [
    "service_category_enc",
    "service_area_enc",
    "interaction_channel_enc",
    "referral_type_enc",
    "neighbourhood_enc",
    "month_number",
    "is_summer",
]

X     = sm.add_constant(df[feature_cols].copy())
y_log = df["log_resolution_days"].copy()

# ── Fit OLS ───────────────────────────────────────────────────────────────────
print("Fitting OLS regression …")
model = sm.OLS(y_log, X).fit()

summary_text = model.summary().as_text()
print(summary_text)

with open(os.path.join(OUT_DIR, "regression_summary.txt"), "w") as f:
    f.write(summary_text)
print("\n  Saved: outputs/regression_summary.txt")

# ── Multicollinearity check ───────────────────────────────────────────────────
print("\n── Variance Inflation Factors ───────────────────────")
X_vif = X.drop(columns=["const"])
vif_df = pd.DataFrame({
    "feature": X_vif.columns,
    "VIF":     [variance_inflation_factor(X_vif.values, i)
                for i in range(X_vif.shape[1])]
}).sort_values("VIF", ascending=False)
print(vif_df.to_string(index=False))

# ── Coefficient export ────────────────────────────────────────────────────────
coef_df = pd.DataFrame({
    "feature":     model.params.index,
    "coefficient": model.params.values,
    "std_err":     model.bse.values,
    "t_stat":      model.tvalues.values,
    "p_value":     model.pvalues.values,
    "ci_lower":    model.conf_int()[0].values,
    "ci_upper":    model.conf_int()[1].values,
}).query("feature != 'const'")

coef_df["significant"] = coef_df["p_value"] < 0.05
coef_df.to_csv(os.path.join(OUT_DIR, "model_coefficients.csv"), index=False)
print("\n  Saved: outputs/model_coefficients.csv")

# ── Coefficient plot ──────────────────────────────────────────────────────────
plot_df = coef_df.sort_values("coefficient")
colors  = ["#2563EB" if s else "#9CA3AF" for s in plot_df["significant"]]

fig, ax = plt.subplots(figsize=(9, 5))
ax.barh(plot_df["feature"], plot_df["coefficient"], color=colors, height=0.6)
ax.errorbar(
    plot_df["coefficient"], range(len(plot_df)),
    xerr=[plot_df["coefficient"] - plot_df["ci_lower"],
          plot_df["ci_upper"]   - plot_df["coefficient"]],
    fmt="none", color="black", linewidth=1.2, capsize=4
)
ax.axvline(0, color="black", linewidth=0.8, linestyle="--")
ax.set_xlabel("Coefficient (log resolution days)")
ax.set_title("OLS Regression Coefficients — 311 Request Resolution Time\n"
             "Blue = p < 0.05 | Grey = not significant")
plt.tight_layout()
fig.savefig(os.path.join(OUT_DIR, "coefficient_plot.png"), dpi=150)
plt.close()
print("  Saved: outputs/coefficient_plot.png")

# ── Key findings ──────────────────────────────────────────────────────────────
print("\n── Model Summary ────────────────────────────────────")
print(f"  R²       : {model.rsquared:.3f}")
print(f"  Adj. R²  : {model.rsquared_adj:.3f}")
print(f"  F-stat   : {model.fvalue:.1f}  (p={model.f_pvalue:.4f})")
print(f"  n        : {int(model.nobs):,}")
print(f"\n  Significant predictors:")
sig = coef_df[coef_df["significant"]].sort_values("coefficient", ascending=False)
for _, row in sig.iterrows():
    direction = "↑ longer" if row["coefficient"] > 0 else "↓ shorter"
    print(f"    {row['feature']:28s}  coef={row['coefficient']:+.3f}  {direction}  p={row['p_value']:.4f}")

print("\nRegression complete.")