# Review and maintenance decisions

| Supplied behavior | Maintained treatment |
| --- | --- |
| Fallback database password in code and fixed Compose credentials | Environment-based password; `.env.example` contains a local placeholder; loopback bindings |
| ETL catches failures and later announces completion | Strict pre-validation and a single transaction; exceptions propagate |
| Malformed numeric values become zero | Reject malformed, missing, fractional and negative counts |
| Territorial cleanup deletes records until expected counts are reached | No count-forcing deletion; reconciliation reports errors |
| 2025 territorial metadata is mixed with 2021 boundaries | Validated normalized input contract; no claim of complete historical territorial reconciliation |
| D'Hondt quotient ties favor larger total votes | Correct lower-vote final-seat rule; unresolved equal-vote ties raise an error |
| Warehouse upserts retain facts removed from operational data | Transactional fact refresh mirrors operational data; dimension attributes update |
| Dashboard selects one arbitrary winner and limits lists used in summaries | Preserve tied winners; complete totals; scope counts by body/territory type |
| Connections close only on the success path | Explicit connection closing after commit or rollback |
| Strings inserted through browser innerHTML | User/data strings written through textContent/text nodes |
| Simplification can invalidate polygon topology | ST_SimplifyPreserveTopology for map output |
| Healthcare overlaps checked only on INSERT with flawed open-interval logic | Half-open intervals checked on both INSERT and UPDATE |
| Year filters miss stays spanning the whole year | Explicit interval-overlap predicates and distinct-patient counting |
| Query 7 contains SSELECT and lists rows rather than ranking doctors | Valid SQL with period grouping and tie-preserving dense ranks |
| dbt schema places a composite test inside a column definition and assumes a missing package | Correct schema YAML plus explicit singular grain tests without dbt-utils |
| dbt history can have duplicate same-day versions or duplicate FX joins | Tests for version uniqueness, positive intervals and unique daily FX keys |

A wide table with atomic party-specific columns is not automatically a violation of first normal form. The maintained election layout uses one row per territory/body/list because it makes changing list sets and aggregations easier; no unsupported normalization or performance guarantee is inferred from that design alone.

## Remaining limits

The election loader expects a complete normalized bundle for the elections it updates, not arbitrary CNE wide files. Its merge does not silently delete omitted operational rows. Database row checks complement application reconciliation; direct SQL writers can still violate cross-row vote-total equality and should run explicit reconciliation. The application uses date-specific schemas without a multi-election year dimension.

Only synthetic geographic examples have been validated in this maintained edition. Importing official national boundaries requires source licensing, temporal identity checks and appropriate CRS treatment. Historical assertions of national row counts/100% coverage are not repeated as verified results.

The healthcare model assumes single-patient rooms and date-level intervals. The dbt mart assumes daily FX and zero opening balances and is not an accounting control system. Passing tests does not establish real-world data correctness or production readiness.
