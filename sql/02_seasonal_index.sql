-- Monthly seasonal index by port, baselined on 2012-2019 (pre-COVID).
-- Index 100 = that port's average month. 130 = 30% above its own average.
-- Baseline excludes 2020 onward so the index measures seasonality,
-- not disruption.
WITH monthly AS (
    SELECT p.port, d.year, d.month_num, d.month_name, SUM(f.teu) AS teu
    FROM fact_container_volume f
    JOIN dim_date d ON d.date_key = f.date_key
    JOIN dim_port p ON p.port_key = f.port_key
    WHERE d.year BETWEEN 2012 AND 2019
    GROUP BY p.port, d.year, d.month_num, d.month_name
),
avg_by_month AS (
    SELECT port, month_num, month_name, AVG(teu) AS avg_month_teu
    FROM monthly GROUP BY port, month_num, month_name
),
avg_overall AS (
    SELECT port, AVG(teu) AS avg_all_months FROM monthly GROUP BY port
)
SELECT a.port, a.month_num, a.month_name,
       ROUND(a.avg_month_teu)                          AS avg_teu,
       ROUND(100.0 * a.avg_month_teu / o.avg_all_months, 1) AS seasonal_index
FROM avg_by_month a
JOIN avg_overall o ON o.port = a.port
ORDER BY a.port, a.month_num;