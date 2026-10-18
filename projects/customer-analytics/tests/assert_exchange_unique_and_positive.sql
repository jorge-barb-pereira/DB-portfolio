select date, currency
from {{ ref('stg_currency_exchange') }}
group by date, currency
having count(*) > 1 or min(base_rate_euro) <= 0 or count(base_rate_euro) <> count(*)
