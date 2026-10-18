-- === IMPORT CTE ===
WITH raw_customers AS (
    SELECT * FROM {{ ref('raw_customers') }}
)

-- === STAGING TRANSFORMATION ===
SELECT 
    CAST(customerID AS INTEGER) AS customer_id,
    CAST(country AS VARCHAR) AS country,
    CAST(state AS VARCHAR) AS state,
    CAST(VIP AS BOOLEAN) AS vip,
    CAST(KYC AS BOOLEAN) AS kyc,
    CAST(wantsNewsletter AS BOOLEAN) AS wants_newsletter,
    CAST(latestUpdate AS DATE) AS latest_update
FROM raw_customers
