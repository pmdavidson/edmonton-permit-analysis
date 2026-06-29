-- 01_service_category_breakdown.sql
-- ------------------------------------------------------------
-- Average and median resolution time by service category.
-- Orders by volume descending so high-impact categories surface first.
-- ------------------------------------------------------------

WITH stats AS (
    SELECT
        service_category,
        COUNT(*)                                                              AS total_requests,
        ROUND(AVG(resolution_days), 1)                                        AS avg_resolution_days,
        ROUND(MIN(resolution_days), 0)                                        AS min_days,
        ROUND(MAX(resolution_days), 0)                                        AS max_days,
        ROUND(AVG(CASE WHEN resolution_days > 7 THEN 1.0 ELSE 0.0 END) * 100, 1)
                                                                              AS pct_over_7_days,
        ROUND(AVG(CASE WHEN resolution_days > 30 THEN 1.0 ELSE 0.0 END) * 100, 1)
                                                                              AS pct_over_30_days
    FROM   requests
    WHERE  resolution_days IS NOT NULL
    GROUP  BY service_category
    HAVING COUNT(*) >= 20
),

ordered AS (
    SELECT
        service_category,
        resolution_days,
        ROW_NUMBER() OVER (PARTITION BY service_category ORDER BY resolution_days) AS rn,
        COUNT(*)     OVER (PARTITION BY service_category)                          AS cnt
    FROM requests
    WHERE resolution_days IS NOT NULL
),

medians AS (
    SELECT
        service_category,
        ROUND(AVG(resolution_days), 1) AS median_resolution_days
    FROM ordered
    WHERE rn IN ((cnt + 1) / 2, (cnt + 2) / 2)
    GROUP BY service_category
)

SELECT
    s.service_category,
    s.total_requests,
    s.avg_resolution_days,
    m.median_resolution_days,
    s.min_days,
    s.max_days,
    s.pct_over_7_days,
    s.pct_over_30_days
FROM   stats s
JOIN   medians m ON m.service_category = s.service_category
ORDER  BY s.total_requests DESC;