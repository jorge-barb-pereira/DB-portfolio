-- === IMPORT CTEs ===
WITH transactions AS (
    SELECT * FROM {{ ref('stg_transactions') }}
),
currency_exchange AS (
    SELECT * FROM {{ ref('stg_currency_exchange') }}
)

-- === INTERMEDIATE TRANSFORMATION ===
SELECT
    t.date,
    t.customer_id,
    t.account_type,
    t.tx_type,
    t.tx_currency,
    t.amount,
    t.amount * c.base_rate_euro AS amount_eur

FROM transactions AS t
LEFT JOIN currency_exchange AS c
    ON t.date = c.date
    AND t.tx_currency = c.currency
    

