-- === IMPORT CTE ===
WITH customers AS (
    SELECT * FROM {{ ref('stg_customers') }}
)

-- === INTERMEDIATE TRANSFORMATION ===
SELECT
    customer_id,
    country,
    state,
    vip,
    kyc,
    wants_newsletter,
    latest_update AS valid_from_date,
    COALESCE(
        LEAD(latest_update) OVER (
            PARTITION BY customer_id 
            ORDER BY latest_update
        ),
        CAST('9999-12-31' AS DATE)
    ) AS valid_to_date
FROM customers
