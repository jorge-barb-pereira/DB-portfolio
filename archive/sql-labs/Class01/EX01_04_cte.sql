WITH DistrictTotals AS (
    -- Step 1: Calculate the window function (the denominator) once.
    SELECT 
        d.id AS district_id,
        d.name AS district_name,
        m.code AS municipality_code,
        m.name AS municipality_name,
        m.mandates,
        -- We compute the total mandates for the district here
        SUM(m.mandates) OVER (PARTITION BY d.id) AS district_total_mandates
    FROM district AS d
    JOIN municipality AS m ON (m.district = d.id)
)
-- Step 2: Perform the final math using the pre-calculated total.
SELECT 
    district_id,
    district_name,
    municipality_code,
    municipality_name,
    mandates,
    district_total_mandates,
    -- Now the division is clean and easy to read:
    ROUND((mandates::numeric / district_total_mandates) * 100, 2) AS mandates_share_percentage
FROM DistrictTotals
ORDER BY district_id, mandates DESC, municipality_name ASC;
