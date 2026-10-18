-- === IMPORT CTE ===
WITH customer_history AS (
    SELECT * FROM {{ ref('int_customer_history') }}
)

-- === MARTS TRANSFORMATION ===
SELECT 
    customer_id,
    country,
    state,
    vip,
    kyc,
    wants_newsletter,
    valid_from_date AS latest_update
FROM customer_history
WHERE valid_to_date = CAST('9999-12-31' AS DATE)
