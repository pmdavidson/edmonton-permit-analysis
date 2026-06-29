-- 04_export_for_powerbi.sql
-- ------------------------------------------------------------
-- Flat export of all closed 311 requests with engineered fields
-- ready for Power BI import.
--
-- Run as:
--   sqlite3 -csv -header data/requests.db < sql/04_export_for_powerbi.sql > outputs/powerbi_export.csv
-- ------------------------------------------------------------

SELECT
    -- Identifiers
    row_id,
    service_category,
    service_area,
    service_description,
    interaction_channel,
    referral_type,

    -- Dates
    date_created,
    date_closed,

    -- Core metric
    resolution_days,
    CASE
        WHEN resolution_days =  0 THEN 'Same day'
        WHEN resolution_days <=  3 THEN '1-3 days'
        WHEN resolution_days <=  7 THEN '4-7 days'
        WHEN resolution_days <= 30 THEN '8-30 days'
        ELSE                            '30+ days'
    END                                             AS resolution_bucket,

    -- Delay flag
    CASE WHEN resolution_days > 7 THEN 1 ELSE 0 END AS is_delayed,

    -- Time dimensions
    CAST(SUBSTR(date_created, 1, 4) AS INTEGER)     AS created_year,
    CAST(SUBSTR(date_created, 6, 2) AS INTEGER)     AS created_month,
    CASE CAST(SUBSTR(date_created, 6, 2) AS INTEGER)
        WHEN 1 THEN 'Jan' WHEN 2 THEN 'Feb' WHEN 3 THEN 'Mar'
        WHEN 4 THEN 'Apr' WHEN 5 THEN 'May' WHEN 6 THEN 'Jun'
        WHEN 7 THEN 'Jul' WHEN 8 THEN 'Aug' WHEN 9 THEN 'Sep'
        WHEN 10 THEN 'Oct' WHEN 11 THEN 'Nov' WHEN 12 THEN 'Dec'
    END                                             AS created_month_name,
    CASE CAST(SUBSTR(date_created, 6, 2) AS INTEGER)
        WHEN 12 THEN 'Winter' WHEN 1 THEN 'Winter' WHEN 2 THEN 'Winter'
        WHEN 3  THEN 'Spring' WHEN 4 THEN 'Spring' WHEN 5 THEN 'Spring'
        WHEN 6  THEN 'Summer' WHEN 7 THEN 'Summer' WHEN 8 THEN 'Summer'
        ELSE 'Fall'
    END                                             AS season,

    -- Location
    neighbourhood,
    ward,
    nbhd_latitude,
    nbhd_longitude

FROM  requests
WHERE resolution_days IS NOT NULL
ORDER BY date_created;