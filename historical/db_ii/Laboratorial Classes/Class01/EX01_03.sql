SELECT
d.id AS district_id,
d.name AS district_name,
m.code AS municipality_code,
m.name AS municipality_name,
m.mandates AS mandates,
RANK() OVER (PARTITION BY d.id ORDER BY m.mandates DESC) AS rank_in_district,
DENSE_RANK() OVER (PARTITION BY d.id ORDER BY m.mandates DESC) AS dense_rank_in_district

FROM district AS d
JOIN municipality AS m ON (m.district = d.id)
ORDER BY district_id, mandates DESC , municipality_name ASC
;

