# Election analytics

The maintained platform adapts the supplied Portuguese local-election database architecture. Operational identifiers retain their Portuguese names for continuity with the original SQL; interfaces and documentation are English.

## Components

- `sql/01_operational_schema.sql`: territories, parties, party results, turnout statistics, keys and spatial indexes.
- `sql/02_functions_triggers.sql`: local coalition and candidate schemas; D'Hondt allocation function.
- `sql/03_data_warehouse_schema.sql`: three dimensions, two fact tables and transactional refresh procedure.
- `sql/04_triggers_views.sql`: result validation, audit records, turnout, vote shares and tied winners.
- `sql/05_analytical_queries.sql`: windows, ROLLUP, CUBE and advanced aggregates. The original real-territory example may produce no rows on the synthetic fixture.
- `sql/06_integrity.sql`: nonnegative counts, geometry validity, territory hierarchy and elected-body consistency.
- `src/election_portfolio/etl.py`: strict CSV validation and atomic import.
- `src/election_portfolio/web.py`: read-only Flask API and dashboard.

The warehouse separates party results from turnout statistics to avoid repeating registered voters once per party. A refresh rebuilds fact rows from current operational records and updates dimension attributes. Dimension keys are retained. An advisory transaction lock serializes application imports/refreshes. Direct administrative writes outside these routines still require coordination.

## Normalized input contract

Four UTF-8, comma-separated files are required. Their exact ordered headers and example values are in `examples/elections/`:

| File | Grain and important rules |
| --- | --- |
| `territories.csv` | One six-digit code; parent must be in the bundle; District → Municipality → Parish hierarchy; optional nonempty WGS84 polygon geometry |
| `parties.csv` | One unique list code and name |
| `statistics.csv` | One territory/body; nonnegative counts, voters <= registered, blank + invalid <= voters |
| `results.csv` | One territory/body/list; integer votes and seats; party totals must equal valid votes |

Bodies CM and AM use municipalities; AF uses parishes. Malformed, missing, fractional and negative counts fail. Ambiguous numeric markers are not silently converted to zero. Territory parents are loaded in order. Source polygons are interpreted as EPSG:4326 and transformed into the retained EPSG:3763 geometry column. PostGIS checks invalid geometry inside the import transaction.

This is an **upsert/merge** loader: omitted operational rows are preserved. For each imported election, stored vote totals are rechecked after the merge; obsolete rows that would break reconciliation cause a rollback. No implicit snapshot deletion is performed. Explicit corrections/deletions are an administrative operation. The warehouse refresh then mirrors the operational facts, including intentional operational deletions.

The new loader does not silently run the original CNE-wide-format parser, territory-count pruning or GIS shell commands. Those selected original scripts are retained as historical references. Adapting an official release requires a documented conversion to this normalized contract, validation of coalition mappings, source checksums, permission to use the data and CRS choices appropriate to each geographic region. EPSG:3763 is not a blanket CRS guarantee for all island datasets. The bundled polygons are synthetic mainland examples.

## D'Hondt behavior

The maintained SQL orders quotients descending and, when a seat-boundary quotient is tied between lists with different total votes, favors the list with **fewer** total votes, following the [CNE explanation](https://www.cne.pt/content/metodo-de-hondt). The original function used descending votes for ties. Exact equal-vote ties at the allocation boundary raise an explicit error requiring external adjudication; alphabetical order is not presented as an official electoral rule. Zero seats returns zero allocations; positive seats with no positive votes are rejected. This function is a portfolio implementation, not an official certification of electoral outcomes.

## API

| Endpoint | Parameters | Output |
| --- | --- | --- |
| `/api/territories` | `orgao=CM/AM/AF` | Available territory codes and names, including records without geometry |
| `/api/map` | `orgao=CM/AM/AF` | GeoJSON in EPSG:4326, preserving tied leaders |
| `/api/results` | `orgao`; optional six-digit `codigo` | Complete list totals, turnout and tied leaders |

Malformed parameters return 400; unavailable territory/body pairs return 404. SQL values are parameterized; connections close after success or failure. Backend errors produce a generic 503 without returning connection strings. Names are placed into browser text nodes rather than unescaped HTML. Map simplification uses [ST_SimplifyPreserveTopology](https://postgis.net/docs/ST_SimplifyPreserveTopology.html). Counts are aggregated at the appropriate territory type to avoid adding district, municipality and parish totals together. National totals retain all lists rather than a top-15 subset.

The Flask development server binds to localhost with debug disabled. Docker exposes PostgreSQL on loopback only. For a hosted deployment, add an appropriate application server, least-privilege database roles, resource limits and operational controls. A public web deployment is outside this repository-conversion task.
