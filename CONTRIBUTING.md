# Contributing

Use Python 3.11+ and run the commands in the README. PostgreSQL integration tests require a fresh dedicated PostGIS database and `RUN_DB_TESTS=1`; they initialize schemas and must not target an existing project database.

Keep documentation and new interfaces in English. Preserve attribution and published historical hashes. Correct historical defects in maintained modules and explain the change in the review document. Do not commit private data, environments, original connection profiles, compiled dbt artifacts or identifying origin metadata. Extend synthetic fixtures and verify observable database behavior when changing SQL or temporal logic.
