# Edmonton 311 Service Request Analysis

## Overview

This project analyzes Edmonton's 311 service request data to identify which request types and neighbourhoods experience the longest resolution delays, quantify the factors driving those delays using regression analysis, and recommend where the city should focus service delivery improvements.

The analysis covers 3.2 million requests submitted between 2023 and 2026, filtered to requests requiring active follow-up (resolution time of 1 day or more) to focus on service delivery rather than information provision.

---

## Problem Statement

Not all 311 requests are equal. Some are resolved same-day, others take months. This analysis asks: **which service categories, neighbourhoods, and time periods experience the longest resolution delays, and what predicts them?**

The answer has direct operational implications. The city can use these findings to allocate field resources, set realistic service level agreements, and identify departments with systemic backlogs.

---

## Key Findings

**City-wide baseline**
- Average resolution time: **3.21 days** across all closed requests requiring follow-up
- **6.79% of requests** take more than 7 days to resolve

**Highest-delay service categories**
- Maintenance - Graffiti spiked to approximately **295 days average in 2024** before dropping sharply, a sign of a temporary backlog that was eventually cleared
- Maintenance - Sidewalk/Concrete, Pavement Markings, and Safety and Security consistently average 40 to 75 days
- Bylaw Complaints and Park Signs show persistently elevated resolution times across all years

![Average Resolution Time by Year and Service Category](outputs/trends.png)

![Distribution of Resolution Times](outputs/resolution_dist.png)

![Resolution Time by Service Category](outputs/service_category_boxplot.png)

**Neighbourhood disparities**
- River Valley Windermere averages **25 days**, nearly 8x the city average
- River Valley neighbourhoods dominate the top 20 slowest, likely due to complex access and maintenance requirements
- South Edmonton Common and Mill Woods Town Centre also appear in the top 20 despite being high-volume commercial areas

![Top 20 Neighbourhoods by Average Resolution Time](outputs/neighbourhood_delays.png)

**What predicts resolution time (OLS Regression)**
- **Referral type** is the dominant predictor. Requests escalated to a department take significantly longer than those resolved with information provided directly
- **Interaction channel** has a negative coefficient, meaning digital channels (app, online) resolve faster than phone
- **Summer** requests take slightly longer, consistent with higher maintenance demand
- Neighbourhood and service category show smaller but consistent effects

![Regression Coefficients](outputs/coefficient_plot.png)

![Model Findings Dashboard](outputs/model_findings.png)

---

## Recommendations

**1. Prioritize digital channel adoption.** The regression shows interaction channel is one of the strongest negative predictors of resolution time, meaning requests submitted through the app or online resolve faster than phone calls. The city should invest in promoting the 311 app in high-volume neighbourhoods to reduce resolution times without adding staff.

**2. Investigate the 2024 Maintenance - Graffiti backlog.** Average resolution time spiked to 295 days in 2024 before returning to normal levels. This pattern suggests a staffing or process disruption rather than a structural problem. A post-mortem on what changed in 2024 and 2025 would clarify whether the improvement is sustainable.

**3. Review referral handling processes.** Referral type is the dominant predictor of resolution time. Requests that get referred to a department take significantly longer than those resolved at first contact. Reducing unnecessary referrals through better first-contact training or expanded agent authority could have the largest overall impact on resolution times.

**4. Target River Valley maintenance resources.** River Valley neighbourhoods account for 7 of the top 20 slowest areas, averaging 12 to 25 days. Given the access and terrain challenges, the city should assess whether current maintenance scheduling and crew allocation for River Valley areas reflects actual demand.

---

## Repository Structure

```
edmonton-311-analysis/
├── data/
│   └── requests.db          # SQLite database (gitignored)
├── sql/
│   ├── 01_service_category_breakdown.sql
│   ├── 02_seasonal_trends.sql
│   ├── 03_neighbourhood_ranking.sql
│   └── 04_export_for_powerbi.sql
├── src/
│   ├── 01_load_data.py      # Download + ingest to SQLite
│   ├── 02_eda.py            # Distribution analysis + Kruskal-Wallis tests
│   └── 03_regression.py     # OLS regression with statsmodels
├── outputs/                 # Generated charts and exports (gitignored)
├── requirements.txt
└── README.md
```

---

## Reproducing the Analysis

**Requirements**

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

**Run in order**

```bash
python src/01_load_data.py   # Downloads 3.2M rows and loads into SQLite
python src/02_eda.py         # EDA, significance tests, feature engineering
python src/03_regression.py  # OLS model, coefficient export
```

**SQL queries**

```bash
sqlite3 data/requests.db < sql/01_service_category_breakdown.sql
sqlite3 data/requests.db < sql/02_seasonal_trends.sql
sqlite3 data/requests.db < sql/03_neighbourhood_ranking.sql
sqlite3 -csv -header data/requests.db < sql/04_export_for_powerbi.sql > outputs/powerbi_export.csv
```

---

## Dashboard

Built in Power BI (web). Three pages:

| Page | Content |
|------|---------|
| **Trends** | Average resolution time by year and service category; slicers for category and year |
| **Neighbourhood Delays** | Top 20 neighbourhoods by average resolution time |
| **Model Findings** | OLS regression coefficients; KPI cards for city-wide avg and % delayed |

---

## Data Source

City of Edmonton Open Data -- 311 Requests  
[https://data.edmonton.ca/City-Administration/311-Requests/q7ua-agfg](https://data.edmonton.ca/City-Administration/311-Requests/q7ua-agfg)

3,197,871 rows. Updated regularly. Analysis run on data through June 2026.