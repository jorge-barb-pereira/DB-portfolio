SELECT 
d.id AS district_id,
d.name AS district_name,
m.code AS municipality_code,
m.name AS municipality_name,
m.mandates,
SUM(m.mandates) OVER (PARTITION BY d.id) AS district_total_mandates,
m.mandates::numeric/SUM(m.mandates) OVER (PARTITION BY d.id) AS mandates_share

FROM district AS d
JOIN municipality AS m ON (m.district = d.id)
ORDER BY district_id, mandates DESC , municipality_name ASC
;
