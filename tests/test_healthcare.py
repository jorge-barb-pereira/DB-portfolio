import importlib.util
from pathlib import Path
import sqlite3
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('healthcare_demo',ROOT/'healthcare/demo.py')
demo = importlib.util.module_from_spec(spec)
spec.loader.exec_module(demo)


class HealthcareTests(unittest.TestCase):
    def setUp(self):
        self.db = demo.demo_connection()

    def tearDown(self):
        self.db.close()

    def test_all_seven_queries_execute(self):
        paths = sorted((ROOT/'healthcare/queries').glob('*.sql'))
        self.assertEqual(len(paths),7)
        for path in paths:
            with self.subTest(query=path.name):
                self.assertTrue(self.db.execute(path.read_text(encoding='utf-8')).fetchall())

    def test_overlap_rejected_for_same_patient(self):
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.execute("INSERT INTO Hospitalization VALUES(10,1,1,4,'2025-01-15','2025-02-15')")

    def test_overlap_rejected_for_same_room(self):
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.execute("INSERT INTO Hospitalization VALUES(10,3,1,1,'2025-01-15','2025-02-15')")

    def test_update_cannot_create_overlap(self):
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.execute("UPDATE Hospitalization SET room_number=3 WHERE hospitalization_id=1")

    def test_adjacent_stays_allowed(self):
        self.db.execute("INSERT INTO Hospitalization VALUES(10,1,1,1,'2025-02-01','2025-02-15')")

    def test_historical_stay_before_open_stay_allowed(self):
        self.db.execute("INSERT INTO Hospitalization VALUES(10,2,2,3,'2024-01-01','2024-02-01')")

    def test_foreign_keys_quantities_and_dates(self):
        for sql in ("INSERT INTO Prescription VALUES(10,99,1,'2025-01-01',1,1)",
                    "INSERT INTO Prescription VALUES(10,1,1,'2025-01-01',1,0)",
                    "INSERT INTO Hospitalization VALUES(10,1,1,1,'2025-02-30','2025-03-10')"):
            with self.subTest(sql=sql),self.assertRaises(sqlite3.IntegrityError):
                self.db.execute(sql)

    def test_annual_query_includes_stay_spanning_entire_year(self):
        self.db.execute("INSERT INTO Patient(patient_id,name,date_of_birth,gender,phone_number) VALUES(8,'Demo Patient 8','1980-01-01','Other',100000008)")
        self.db.execute("INSERT INTO Hospitalization VALUES(10,8,1,4,'2024-12-01','2026-01-01')")
        rows=self.db.execute((ROOT/'healthcare/queries/02_query.sql').read_text()).fetchall()
        self.assertEqual(dict(rows)['Cardiology'],3)

