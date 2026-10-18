# Provenance, dates and source coverage

Maintained/imported on **18 October 2026** from the user-supplied database coursework collection. Originals remain untouched. The public repository is a separate checkout; it does not include any nested source Git history.

## Development dates

The supplied election report and project README identify the **2025/2026 Advanced Topics in Databases** coursework. They credit **Jorge Pereira, Rafael Martins and Sofia Gonçalves**. Individual contribution boundaries are not independently established. Student identifiers and original report documents are not published. The **2021** in the election title identifies the dataset, not when the code was written.

Filesystem timestamps for selected sources are recorded in `historical/manifest.json`. Many are September/October 2026 copy timestamps, so they are not treated as proof of original development dates. Earlier healthcare SQL references 2025 analysis periods; those date predicates likewise do not prove authorship dates. The generic dbt study's original development date is unconfirmed. Maintained changes use genuine current Git commits.

## Source coverage

| Supplied material | Public treatment |
| --- | --- |
| Latest election SQL | Adapted into `sql/`, with original copies in `historical/Project/sql/` |
| Election Python/HTML | Selected original source preserved historically; maintained ETL and web modules have explicit validation and lifecycle management |
| Earlier election backups | Duplicate snapshots excluded; latest supplied implementation is the working baseline |
| DB I healthcare schema and seven queries | Preserved historically; runnable fixes, synthetic records and tests in `healthcare/` |
| Earlier DB I schema/query drafts | Selected SQL retained historically; population scripts omitted |
| DB II laboratory SQL | Selected exercises in `historical/`; instructor-solution files excluded |
| Customer dbt transformations | Generic model SQL adapted; all original seed records, profiles and identifying context excluded |
| Public dbt-course models | Seven SQL references preserved separately with upstream attribution and supplied license |
| Lecture slides, assignment PDFs, reports, ZIP archives, IDE state, environments and database dumps | Excluded |
| Original geographic/election/customer/healthcare data | Excluded; public runnable examples are synthetic |

The import manifest contains the original and published SHA-256 values for selected non-private historical files. Fallback and inline database passwords were replaced with environment lookups in historical Python configuration; such transformations are explicitly recorded. No `.env` or connection profile was copied. `tools/audit_sources.py` verifies the published hashes.

The generic dbt provenance records only selected model hashes and neutral public paths; private source locations and identifying origin metadata are deliberately withheld. The public code documents its technical transformations without exposing their original context. `tools/import_sources.py` reimports only the explicitly selected non-private historical baseline. It does not overwrite maintained modules or export private dbt content.
