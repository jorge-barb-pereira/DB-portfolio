select customer_id, valid_from_date
from {{ ref('int_customer_history') }}
group by customer_id, valid_from_date
having count(*) > 1 or min(valid_to_date) <= valid_from_date
