-- Annual TEU and year-on-year growth, with a completeness flag.
-- A year is 'complete' only if all 12 months are present AND all 9 ports
-- reported in every month. This is what stops the Auckland series break
-- being read as a demand collapse.
WITH annual AS (
    SELECT d.year,
           SUM(f.teu)                 AS teu,
           COUNT(DISTINCT d.date_key) AS months_in_year,
           MIN(d.ports_reporting)     AS min_ports_reporting
    FROM fact_container_volume f
    JOIN dim_date d ON d.date_key = f.date_key
    GROUP BY d.year
)
SELECT year,
       teu,
       months_in_year,
       min_ports_reporting,
       LAG(teu) OVER (ORDER BY year) AS prev_teu,
       ROUND(100.0 * (teu - LAG(teu) OVER (ORDER BY year))
             / LAG(teu) OVER (ORDER BY year), 1) AS yoy_pct,
       CASE WHEN months_in_year = 12 AND min_ports_reporting = 9
            THEN 'complete' ELSE 'incomplete' END AS status
FROM annual
ORDER BY year;