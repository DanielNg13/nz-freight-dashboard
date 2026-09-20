-- Share of TEU that is empty, by port and direction.
-- Empty containers are repositioning moves: they consume berth, yard and
-- road capacity but carry no cargo. The import/export asymmetry shows
-- which ports need empties brought IN and which need them taken OUT.
WITH pt AS (
    SELECT p.port, t.trade, d.year,
           SUM(CASE WHEN f.load_status = 'Empty' THEN f.teu ELSE 0 END) AS empty_teu,
           SUM(f.teu) AS total_teu
    FROM fact_container_volume f
    JOIN dim_date  d ON d.date_key  = f.date_key
    JOIN dim_port  p ON p.port_key  = f.port_key
    JOIN dim_trade t ON t.trade_key = f.trade_key
    WHERE d.year BETWEEN 2012 AND 2024
    GROUP BY p.port, t.trade, d.year
)
SELECT port, trade, year, empty_teu, total_teu,
       ROUND(100.0 * empty_teu / total_teu, 1) AS empty_pct
FROM pt
ORDER BY port, trade, year;