WITH MunicipalityStats AS (
    -- Step 1: Pre-aggregate all municipality data by district
    SELECT 
        district,
        COUNT(code) AS total_municipalities,
        COUNT(code) FILTER (WHERE mandates > 10) AS municipalities_with_mandates
    FROM municipality
    GROUP BY district
)
-- Step 2: Join the pre-aggregated stats to the dimension table (district)
SELECT 
    d.id,
    d.name,
    ms.total_municipalities,
    ms.municipalities_with_mandates
FROM district AS d
JOIN MunicipalityStats AS ms ON (ms.district = d.id)
ORDER BY d.id;
