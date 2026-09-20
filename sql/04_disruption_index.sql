-- Rolling 12-month average TEU, indexed to the 2019 monthly average.
--
-- Uses only the 8 ports with unbroken series (series_ends_early = 0),
-- so the index is comparable across the whole period. Auckland is
-- deliberately excluded here - including it would make the index fall
-- off a cliff in mid-2025 for reporting reasons, not freight reasons.
--
-- The rolling average smooths seasonality so the disruption signal
-- is readable. n_in_window = 12 drops the first 11 partial windows.
WITH monthly AS (
    SELECT d.date_key, d.month_label, d.year, SUM(f.teu) AS teu
    FROM fact_container_volume f
    JOIN dim_date d ON d.date_key = f.date_key
    JOIN dim_port p ON p.port_key = f.port_key
    WHERE p.series_ends_early = 0
    GROUP BY d.date_key, d.month_label, d.year
),
rolling AS (
    SELECT *,
           AVG(teu) OVER (ORDER BY date_key
                          ROWS BETWEEN 11 PRECEDING AND CURRENT ROW) AS roll12,
           COUNT(*) OVER (ORDER BY date_key
                          ROWS BETWEEN 11 PRECEDING AND CURRENT ROW) AS n_in_window
    FROM monthly
),
base AS (
    SELECT AVG(teu) AS base_2019 FROM monthly WHERE year = 2019
)
SELECT r.month_label,
       r.teu,
       ROUND(r.roll12)                          AS roll12_teu,
       ROUND(100.0 * r.roll12 / b.base_2019, 1) AS idx_vs_2019
FROM rolling r
CROSS JOIN base b
WHERE r.n_in_window = 12
ORDER BY r.date_key;