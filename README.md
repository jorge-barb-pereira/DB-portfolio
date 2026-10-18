# Advanced Databases Portfolio

Three independent database projects, each with its own setup, dependencies, tests and documentation. Choose a project below; nothing at the repository root installs or starts an application.

| Project | Focus | Runtime | Checks |
| --- | --- | --- | --- |
| [Election Analytics](projects/election-analytics/) | Atomic ETL, relational and dimensional modeling, PL/pgSQL, spatial queries and a dashboard | Python + PostgreSQL/PostGIS + Flask | [![Election checks](https://github.com/jorge-barb-pereira/advanced-databases-portfolio/actions/workflows/elections.yml/badge.svg)](https://github.com/jorge-barb-pereira/advanced-databases-portfolio/actions/workflows/elections.yml) |
| [Healthcare Database](projects/healthcare-db/) | Relational constraints, admission intervals and seven analytical queries | Python standard library + SQLite | [![Healthcare checks](https://github.com/jorge-barb-pereira/advanced-databases-portfolio/actions/workflows/healthcare.yml/badge.svg)](https://github.com/jorge-barb-pereira/advanced-databases-portfolio/actions/workflows/healthcare.yml) |
| [Customer Analytics](projects/customer-analytics/) | dbt transformations, effective-date history, FX conversion and running balances | dbt + DuckDB | [![Customer checks](https://github.com/jorge-barb-pereira/advanced-databases-portfolio/actions/workflows/customer-analytics.yml/badge.svg)](https://github.com/jorge-barb-pereira/advanced-databases-portfolio/actions/workflows/customer-analytics.yml) |

## Repository layout

```text
projects/
  election-analytics/     README, Python package, SQL, synthetic CSVs, Docker and tests
  healthcare-db/         README, SQLite schema, demo, seven queries and tests
  customer-analytics/    README, dbt project, models, synthetic seeds, tests and tools
archive/                 Historical SQL/source and separately attributed course references
docs/                    Portfolio-wide provenance, review and validation
tools/                   Repository-wide source integrity audit
.github/workflows/       Independent workflows scoped to each project
```

Enter the chosen project directory and follow its README. Use a separate virtual environment per project to keep Flask/PostgreSQL dependencies independent of dbt/DuckDB. The healthcare demo needs no third-party packages. The projects share no application configuration, database credentials or runtime imports.

## Background and source material

The election coursework identifies the **2025/2026 academic year**. The original election dataset describes **2021**, not the development date. Exact original dates for the smaller healthcare and generic dbt studies are unconfirmed. **Maintained edition: October 2026.** See [provenance and credits](docs/PROVENANCE.md).

Public runnable examples contain invented records and geometries. Original seed datasets, connection profiles, environments, compiled artifacts and identifying private context are excluded. The [archive](archive/) is historical reference material; its code is not installed or executed by the active projects. Course files retain their own attribution and license.

Read the [review](docs/REVIEW.md), [validation record](docs/VALIDATION.md), [attribution notice](THIRD_PARTY_NOTICES.md) and [contributing guide](CONTRIBUTING.md). Passing synthetic-data tests does not certify official election results, clinical workflows or accounting balances.
