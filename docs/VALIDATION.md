# Validation record

Maintained edition reviewed on 18 October 2026. The test suite separates self-contained checks from a real PostgreSQL/PostGIS integration run. Skipped database tests are not counted as passes.

## Local checks

Windows, Python 3.12.14:

- **18 Python/SQLite checks passed**: all seven healthcare queries; patient and room overlaps; update conflicts; adjacent and past stays; foreign keys, quantities and dates; year-spanning admissions; normalized bundle validation; invalid/duplicate counts and rows; hierarchy/body consistency; English dashboard; malformed API parameters; required password configuration.
- The source audit passed for **38 selected historical files**, including explicitly recorded configuration sanitization.
- The synthetic election bundle validated: **5 territories, 3 lists, 18 party-result rows and 6 turnout records**.
- **dbt build passed all 40 nodes**: 3 synthetic seeds, 7 models and **30 data tests**, with no warnings or errors. Runtime: dbt-core 1.12.6, dbt-duckdb 1.11.0, DuckDB 1.5.6.
- Independent dbt result checks verify hand-calculated FX values, a customer-state date boundary, latest state, daily grain and separate account balances.

Docker/PostgreSQL is not installed in the local Windows shell. The nine database checks require `RUN_DB_TESTS=1` and a new dedicated database; they are explicitly skipped locally. Real database behavior is verified in the GitHub Actions PostGIS job before reporting remote success.

## PostgreSQL/PostGIS integration coverage

The workflow provisions `postgis/postgis:16-3.4` and checks:

1. Correct D'Hondt quotient tie handling on a synthetic known allocation.
2. Explicit failure for an unresolved equal-vote seat-boundary tie.
3. Rejection of negative counts by actual PostgreSQL constraints/triggers.
4. Repeat-import idempotence and expected operational/warehouse counts.
5. Removal of stale warehouse facts after an operational deletion.
6. Audit capture of old/new vote values.
7. Real spatial transformation/GeoJSON output and API totals/tied leaders.
8. Execution of every maintained analytical SQL query.
9. Rollback of earlier updates when later geometry fails validation.

The workflow also runs the unit suite on Python 3.11/3.12 and builds/tests dbt on a separate runner. CI passwords are disposable test-only values, not copied source credentials. No original private profile or external warehouse account is needed.

## GitHub verification after project isolation

Implementation commit `58b9309` completed all four independent workflows successfully:

| Project/check | Actual remote result |
| --- | --- |
| [Election analytics](https://github.com/jorge-barb-pereira/advanced-databases-portfolio/actions/runs/39132393357) | 10 self-contained checks pass on Python 3.11/3.12; all 19 election checks pass with the real PostgreSQL 16/PostGIS service, including the nine database integration checks |
| [Healthcare database](https://github.com/jorge-barb-pereira/advanced-databases-portfolio/actions/runs/39132393383) | All eight SQLite checks and all seven demo queries pass on Python 3.11 and 3.12 |
| [Customer analytics](https://github.com/jorge-barb-pereira/advanced-databases-portfolio/actions/runs/39132393462) | All three synthetic seeds, seven models and 30 dbt data tests pass; independent hand-calculated result checks pass |
| [Source integrity](https://github.com/jorge-barb-pereira/advanced-databases-portfolio/actions/runs/39132393413) | All 38 selected archived-source hashes and repository packaging checks pass |

The first integration run identified a PL/pgSQL CASE-expression grouping error in the new hierarchy/body triggers. Parenthesizing those expressions corrected it; the successful real-database run above verifies the final SQL rather than treating the original failure as a pass.

Each project now has its own working directory, dependency setup and path-scoped workflow. Shared root tooling uses the standard library and does not import project runtimes. Local verification also passed from the reorganized project directories. The GitHub layout was prepared in a separate publishing checkout; the user's existing local project folders were not reorganized.

The selected public files were additionally scanned for known supplied secret values, identifying private-origin markers and student identifiers. Original profiles, source data and generated dbt artifacts were excluded. The scan is a packaging check, not a guarantee about future contributions.

## Scope limits

Tests use invented, small datasets. They do not verify the original README's national data counts, official election outcomes, complete geographic coverage, real clinical workflows or production accounting balances. The historical destructive cleanup and stale-configuration patterns remain visible only as documented original source; those scripts are not run by tests or the maintained CLI.
