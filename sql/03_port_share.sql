-- Each port's share of national TEU by year.
-- Restricted to 2012-2024: 2025 and 2026 are excluded because Auckland
-- stops reporting in Jun 2025, which would inflate every other port's share.
WITH port_year AS (
    SELECT d.year, p.port, SUM(f.teu) AS teu
    FROM fact_container_volume f
    JOIN dim_date d ON d.date_key = f.date_key
    JOIN dim_port p ON p.port_key = f.port_key
    WHERE d.year BETWEEN 2012 AND 2024
    GROUP BY d.year, p.port
),
year_total AS (
    SELECT year, SUM(teu) AS total_teu FROM port_year GROUP BY year
)
SELECT y.year, y.port, y.teu,
       ROUND(100.0 * y.teu / t.total_teu, 1) AS share_pct
FROM port_year y
JOIN year_total t ON t.year = y.year
ORDER BY y.year, share_pct DESC;