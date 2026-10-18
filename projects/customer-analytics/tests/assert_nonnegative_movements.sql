select amount as invalid_value from {{ ref('stg_transactions') }} where amount<0
union all
select deposit from {{ ref('fct_transactions') }} where deposit<0 or withdrawal<0
