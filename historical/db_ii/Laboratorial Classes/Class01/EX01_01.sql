WITH RECURSIVE tb01 AS (

-- 1. Ancor member: produces the initial row(s)

SELECT 1 AS i

UNION ALL

-- 2. Recursive member: refers to the CTE itself

SELECT i + 1 FROM tb01

WHERE i < 20 -- Note: using < 20 ensures we stop exactly at 20. If we use <= 20, it will generate 21.
)

SELECT * FROM tb01
ORDER BY i;