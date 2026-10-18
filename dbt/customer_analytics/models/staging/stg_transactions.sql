-- === IMPORT CTE ===
WITH raw_transactions AS (
    SELECT * FROM {{ ref('raw_transactions') }}
)

-- === STAGING TRANSFORMATION ===
SELECT
    CAST(date AS DATE) AS date,
    CAST(customerId AS INTEGER) AS customer_id,
    CAST(accountType AS INTEGER) AS account_type,
    CAST(amount AS NUMERIC(30, 15)) AS amount,
    CAST(channelUID AS VARCHAR) AS channel_uid,
    CAST(txCurrency AS VARCHAR) AS tx_currency,
    CAST(txType AS VARCHAR) AS tx_type
FROM raw_transactions
