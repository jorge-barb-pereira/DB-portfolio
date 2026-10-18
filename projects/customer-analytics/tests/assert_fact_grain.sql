select date,customer_id,account_type
from {{ ref('fct_transactions') }}
group by date,customer_id,account_type having count(*)>1
