# Contributing

Each runnable project is independent. Enter its directory, create its own virtual environment if needed and follow its README. Do not add shared runtime dependencies at the portfolio root.

- Election analytics: Python/Flask/PostgreSQL/PostGIS; run its Python suite from `projects/election-analytics/`.
- Healthcare database: Python standard library/SQLite; run its demo and suite from `projects/healthcare-db/`.
- Customer analytics: dbt/DuckDB; run its build and independent result checks from `projects/customer-analytics/`.

PostgreSQL integration tests require a fresh dedicated PostGIS database and `RUN_DB_TESTS=1`; never point them at an existing project database. CI workflows are scoped to project paths and use independent dependency environments.

Keep new interfaces/documentation in English, preserve attribution and archived hashes, and explain substantive fixes in the review document. Never commit original data, credentials, private profiles, environments, generated artifacts or identifying origin metadata. Shared tooling at the root must stay independent of project runtimes.
