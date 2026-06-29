-- 02_seasonal_trends.sql
-- ------------------------------------------------------------
-- Monthly and seasonal patterns in 311 request resolution times.
-- Identifies whether delays cluster in certain months or seasons.
-- ------------------------------------------------------------

WITH monthly AS (
    SELECT
        SUBSTR(date_created, 1, 7)                      AS year_month,
        CAST(SUBSTR(date_created, 6, 2) AS INTEGER)     AS month_num,
        CAST(SUBSTR(date_created, 1, 4) AS INTEGER)     AS year,
        COUNT(*)                                        AS total_requests,
        ROUND(AVG(resolution_days), 1)                  AS avg_resolution_days,
        SUM(CASE WHEN resolution_days > 7 THEN 1 ELSE 0 END) AS delayed_count
    FROM   requests
    WHERE  resolution_days IS NOT NULL
      AND  date_created IS NOT NULL
    GROUP  BY year_month
),

seasonal AS (
    SELECT
        CASE month_num
            WHEN 12 THEN 'Winter' WHEN 1 THEN 'Winter' WHEN 2 THEN 'Winter'
            WHEN 3  THEN 'Spring' WHEN 4 THEN 'Spring' WHEN 5 THEN 'Spring'
            WHEN 6  THEN 'Summer' WHEN 7 THEN 'Summer' WHEN 8 THEN 'Summer'
            ELSE 'Fall'
        END                                             AS season,
        ROUND(AVG(avg_resolution_days), 1)              AS avg_resolution_days,
        SUM(total_requests)                             AS total_requests,
        SUM(delayed_count)                              AS total_delayed
    FROM   monthly
    GROUP  BY season
)

-- Monthly trend — use this for Power BI line chart
SELECT
    year_month,
    total_requests,
    avg_resolution_days,
    ROUND(CAST(delayed_count AS REAL) / total_requests * 100, 1) AS pct_delayed
FROM   monthly
ORDER  BY year_month;

-- Uncomment for seasonal summary:
-- SELECT *, ROUND(CAST(total_delayed AS REAL) / total_requests * 100, 1) AS pct_delayed
-- FROM seasonal ORDER BY avg_resolution_days DESC;