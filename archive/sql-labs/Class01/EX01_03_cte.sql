WITH RankedMunicipalities AS (
    -- Step 1: Isolate the analytical logic on the base table.
    SELECT 
        district AS district_id,
        code AS municipality_code,
        name AS municipality_name,
        mandates,
        RANK() OVER (PARTITION BY district ORDER BY mandates DESC) AS rank_in_district,
        DENSE_RANK() OVER (PARTITION BY district ORDER BY mandates DESC) AS dense_rank_in_district
    FROM municipality
)
-- Step 2: Enrichment. 
SELECT 
    d.id AS district_id,
    d.name AS district_name,
    rm.municipality_code,
    rm.municipality_name,
    rm.mandates,
    rm.rank_in_district,
    rm.dense_rank_in_district
FROM district AS d
JOIN RankedMunicipalities AS rm ON (rm.district_id = d.id)
-- Adding this WHERE clause as an example of why CTEs are powerful here
-- WHERE rm.dense_rank_in_district <= 3
ORDER BY d.id, rm.mandates DESC, rm.municipality_name ASC;