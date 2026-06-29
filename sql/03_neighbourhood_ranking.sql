-- 03_neighbourhood_ranking.sql
-- ------------------------------------------------------------
-- Ranks neighbourhoods by average resolution time using window
-- functions. Calculates deviation from the city-wide average
-- and assigns quartiles — Q1 = worst delays, Q4 = best.
-- ------------------------------------------------------------

WITH neighbourhood_stats AS (
    SELECT
        neighbourhood,
        COUNT(*)                        AS total_requests,
        ROUND(AVG(resolution_days), 1)  AS avg_resolution_days,
        ROUND(MIN(resolution_days), 0)  AS min_days,
        ROUND(MAX(resolution_days), 0)  AS max_days,
        SUM(CASE WHEN resolution_days > 7 THEN 1 ELSE 0 END) AS delayed_count
    FROM   requests
    WHERE  resolution_days IS NOT NULL
      AND  neighbourhood IS NOT NULL
      AND  neighbourhood != ''
    GROUP  BY neighbourhood
    HAVING COUNT(*) >= 20
),

ranked AS (
    SELECT
        *,
        RANK() OVER (ORDER BY avg_resolution_days DESC)             AS delay_rank,
        ROUND(AVG(avg_resolution_days) OVER (), 1)                  AS city_avg_days,
        ROUND(avg_resolution_days - AVG(avg_resolution_days) OVER (), 1)
                                                                    AS days_above_city_avg,
        NTILE(4) OVER (ORDER BY avg_resolution_days DESC)           AS delay_quartile,
        ROUND(CAST(delayed_count AS REAL) / total_requests * 100, 1) AS pct_delayed
    FROM   neighbourhood_stats
)

SELECT
    delay_rank,
    neighbourhood,
    total_requests,
    avg_resolution_days,
    city_avg_days,
    days_above_city_avg,
    delay_quartile,
    pct_delayed
FROM   ranked
ORDER  BY delay_rank;