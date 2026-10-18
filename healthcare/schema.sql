PRAGMA foreign_keys = ON;

CREATE TABLE Patient (
    patient_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    date_of_birth TEXT NOT NULL,
    gender TEXT NOT NULL CHECK(gender IN ('Male','Female','Other')),
    phone_number INTEGER NOT NULL CHECK(typeof(phone_number)='integer' AND phone_number BETWEEN 100000000 AND 999999999),
    email TEXT CHECK(email LIKE '%@%'),
    street TEXT, number TEXT, floor TEXT, zip_code TEXT, city TEXT,
    emergency_contact INTEGER CHECK(emergency_contact BETWEEN 100000000 AND 999999999)
);
CREATE TABLE Doctor (
    doctor_id INTEGER PRIMARY KEY,name TEXT NOT NULL,specialty TEXT NOT NULL,
    phone_number INTEGER NOT NULL CHECK(phone_number BETWEEN 100000000 AND 999999999),
    email TEXT NOT NULL CHECK(email LIKE '%@%')
);
CREATE TABLE Hospitalization (
    hospitalization_id INTEGER PRIMARY KEY,
    patient_int INTEGER NOT NULL REFERENCES Patient(patient_id),
    doctor_resp INTEGER NOT NULL REFERENCES Doctor(doctor_id),
    room_number INTEGER NOT NULL CHECK(room_number BETWEEN 1 AND 10),
    admission_date TEXT NOT NULL CHECK(admission_date GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]' AND date(admission_date) IS NOT NULL AND date(admission_date,'+0 days')=admission_date),
    discharge_date TEXT CHECK(discharge_date IS NULL OR
        (discharge_date GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]' AND date(discharge_date) IS NOT NULL AND date(discharge_date,'+0 days')=discharge_date AND discharge_date>admission_date))
);
CREATE TABLE Medication (medication_id INTEGER PRIMARY KEY,name TEXT NOT NULL,type TEXT);
CREATE TABLE Prescription (
    prescription_id INTEGER PRIMARY KEY,
    patient_presc INTEGER NOT NULL REFERENCES Patient(patient_id),
    doctor_presc INTEGER NOT NULL REFERENCES Doctor(doctor_id),
    date_presc TEXT NOT NULL,
    medication_id INTEGER NOT NULL REFERENCES Medication(medication_id),
    quantity INTEGER NOT NULL CHECK(typeof(quantity)='integer' AND quantity>0)
);
-- Half-open stays [admission, discharge); an open stay has no upper bound.
-- Check both INSERT and UPDATE and exclude the updated row itself.
CREATE TRIGGER prevent_overlap_insert BEFORE INSERT ON Hospitalization
WHEN EXISTS(SELECT 1 FROM Hospitalization h
    WHERE (h.patient_int=NEW.patient_int OR h.room_number=NEW.room_number)
      AND NEW.admission_date<coalesce(h.discharge_date,'9999-12-31')
      AND h.admission_date<coalesce(NEW.discharge_date,'9999-12-31'))
BEGIN SELECT RAISE(ABORT,'Overlapping patient or room admission'); END;
CREATE TRIGGER prevent_overlap_update BEFORE UPDATE ON Hospitalization
WHEN EXISTS(SELECT 1 FROM Hospitalization h WHERE h.hospitalization_id<>OLD.hospitalization_id
      AND (h.patient_int=NEW.patient_int OR h.room_number=NEW.room_number)
      AND NEW.admission_date<coalesce(h.discharge_date,'9999-12-31')
      AND h.admission_date<coalesce(NEW.discharge_date,'9999-12-31'))
BEGIN SELECT RAISE(ABORT,'Overlapping patient or room admission'); END;
