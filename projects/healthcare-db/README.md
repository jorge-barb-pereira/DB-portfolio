# SQLite Healthcare Database

A maintained edition of the smaller DB I project: patients, doctors, hospitalizations, medications and prescriptions, with seven analytical queries.

Run from `projects/healthcare-db/`; Python 3.11+ is sufficient and no package installation is required.

```bash
python demo.py
python -m unittest discover -s tests -p test_healthcare.py -v
```

The demo creates an in-memory database using only Python's standard library. All names, contact details, admissions and medicines are invented; example email addresses use `example.invalid`. No original population script is distributed.

| Query | Question |
| --- | --- |
| 1 | Which patients have an open admission and which room are they in? |
| 2 | Which specialties treated the most distinct admitted patients during 2025, including stays spanning the year? |
| 3 | Which medicines were prescribed to demo patient 3, newest first? |
| 4 | What quantities were prescribed per medicine? |
| 5 | What is demo patient 7's admission history? |
| 6 | Which demo room 9 stays overlap September 2025? |
| 7 | Which doctors admitted the most distinct patients in January–April and May–August 2025, preserving ties? |

Stays use half-open intervals `[admission, discharge)`. A null discharge means an open interval, not that every past date overlaps. Triggers check both patient and room conflicts on INSERT and UPDATE, excluding the updated row itself. Discharge at the next admission time is allowed. The exercise assumes one patient per room; real multi-bed room modeling would require another entity. Dates are ISO calendar dates; this is not a time-of-day scheduling system.

The maintained version fixes the original `SSELECT` typo, replaces query 7's raw listings with grouped rankings, corrects year/period-overlap predicates and enables foreign keys. Original current and earlier schemas/queries remain under [the healthcare archive](../../archive/healthcare-db/). Their presence documents development, not production readiness. Clinical workflow validation and use of real patient records are outside this synthetic academic demonstration.
