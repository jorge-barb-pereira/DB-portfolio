# Historical source and course references

This directory is an archive, not a runtime or installable package. Active projects never import or execute it.

| Folder | Contents |
| --- | --- |
| `election-analytics/` | Selected original election SQL, ETL and dashboard sources, with documented credential sanitization |
| `healthcare-db/` | Original SQLite schema/query revisions; original population scripts excluded |
| `sql-labs/` | Selected academic SQL exercises; instructor solutions excluded |
| `dbt-course-airbnb/` | Separately attributed course-model references and their supplied license |
| `tools/` | Historical-source import utility; does not overwrite maintained projects |

Known defects remain visible for provenance. Some original scripts contain destructive cleanup or unsafe data-handling patterns; use the maintained projects for runnable demonstrations. `manifest.json` records original/published hashes and changes. Run `python tools/audit_sources.py` from the repository root to verify the selected archived source.
