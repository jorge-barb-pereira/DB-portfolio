"""Build the generic dbt demo with generated local-only DuckDB settings."""
import os
from pathlib import Path
import shutil

ROOT=Path(__file__).resolve().parents[1]
output=ROOT/'output/dbt'
profiles=output/'profiles'
profiles.mkdir(parents=True,exist_ok=True)
shutil.copyfile(ROOT/'profiles.example.yml',profiles/'profiles.yml')
os.environ['DBT_DEMO_PATH']=(output/'analytics.duckdb').as_posix()
os.environ['DBT_SEND_ANONYMOUS_USAGE_STATS']='false'
os.environ['DBT_USE_COLORS']='false'

from dbt.cli.main import dbtRunner

result=dbtRunner().invoke(['build','--project-dir',str(ROOT),
    '--profiles-dir',str(profiles),'--target-path',str(output/'target'),
    '--log-path',str(output/'logs')])
if not result.success:
    raise SystemExit('dbt build failed; inspect output/dbt/logs locally')
