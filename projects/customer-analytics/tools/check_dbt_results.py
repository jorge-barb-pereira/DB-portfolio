"""Check independently hand-calculated FX, temporal-boundary and balance results."""
from decimal import Decimal
from pathlib import Path
import duckdb

ROOT=Path(__file__).resolve().parents[1]
with duckdb.connect(str(ROOT/'output/dbt/analytics.duckdb'),read_only=True) as connection:
    rows=connection.execute('''select date::varchar,customer_id,country,account_type,deposit,withdrawal,balance
        from analytics.analytics.fct_transactions order by date,customer_id,account_type''').fetchall()
    expected=[('2025-01-15',101,'AA',1,90,20,70),('2025-02-01',101,'BB',1,50,0,120),
              ('2025-02-02',202,'CC',2,200,0,200),('2025-02-03',101,'BB',2,23,0,23)]
    assert len(rows)==len(expected),(rows,expected)
    for actual,wanted in zip(rows,expected):
        assert actual[:4]==wanted[:4],(actual,wanted)
        assert all(a==Decimal(w) for a,w in zip(actual[4:],wanted[4:])),(actual,wanted)
    latest=connection.execute('select country from analytics.analytics.dim_customers where customer_id=101').fetchone()[0]
    assert latest=='BB'
print('dbt business-result checks passed: FX, date boundary, latest state, daily grain and account-isolated balances.')
