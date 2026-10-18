select * from {{ ref('stg_currency_exchange') }} where currency='EUR' and base_rate_euro<>1
