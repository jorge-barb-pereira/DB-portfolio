-- === IMPORT CTE ===
WITH raw_currency_exchange AS (
    SELECT * FROM {{ ref('raw_currency_exchange') }}
)

-- === STAGING TRANSFORMATION ===
SELECT
    CAST(date AS DATE) AS date,
    CAST(currency AS VARCHAR) AS currency,
    CAST(baseRateEuro AS NUMERIC(30, 15)) AS base_rate_euro
FROM raw_currency_exchange
