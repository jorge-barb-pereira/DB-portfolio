-- === IMPORT CTEs ===
WITH transactions AS (
    SELECT * FROM {{ ref('int_transactions_converted') }}
),
customer_history AS (
    SELECT * FROM {{ ref('int_customer_history') }}
),

-- === TEMPORAL JOIN & PRE-AGGREGATION ===
joined_transactions AS (
    SELECT
        t.date AS date,
        t.customer_id,
        c.country,
        t.account_type,
        CASE WHEN t.tx_type = 'DEPOSIT' THEN t.amount_eur ELSE 0 END AS deposit_amount,
        CASE WHEN t.tx_type = 'WITHDRAWAL' THEN t.amount_eur ELSE 0 END AS withdrawal_amount
    FROM transactions AS t
    INNER JOIN customer_history AS c
        ON t.customer_id = c.customer_id
        AND t.date >= c.valid_from_date
        AND t.date < c.valid_to_date
),

-- === DAILY AGGREGATION ===
daily_aggregation AS (
    SELECT
        date,
        customer_id,
        country,
        account_type,
        SUM(deposit_amount) AS deposit,
        SUM(withdrawal_amount) AS withdrawal
    FROM joined_transactions
    GROUP BY date, customer_id, country, account_type
)

-- === FINAL MARTS TRANSFORMATION (RUNNING BALANCE) ===
SELECT
    date,
    customer_id,
    country,
    account_type,
    deposit,
    withdrawal,
    SUM(deposit - withdrawal) OVER (
        PARTITION BY customer_id, account_type 
        ORDER BY date
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) AS balance
FROM daily_aggregation
ORDER BY customer_id, account_type, date
