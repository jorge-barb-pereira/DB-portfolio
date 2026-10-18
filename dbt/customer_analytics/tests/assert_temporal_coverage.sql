select t.customer_id,t.date
from {{ ref('int_transactions_converted') }} t
left join {{ ref('int_customer_history') }} c
on t.customer_id=c.customer_id and t.date>=c.valid_from_date and t.date<c.valid_to_date
where c.customer_id is null
