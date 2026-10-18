SELECT
d.id,
d.name,
COUNT(m.code),
COUNT(m.code) FILTER (WHERE m.mandates > 10) AS municipalities_with_mandates
FROM district AS d
JOIN municipality as m ON (m.district = d.id)
GROUP BY d.id, d.name
ORDER BY d.id
;