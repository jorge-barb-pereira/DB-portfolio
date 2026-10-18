
-- DDL: Data Definition Language
DROP TABLE IF EXISTS Patient;
DROP TABLE IF EXISTS Doctor;
DROP TABLE IF EXISTS Hospitalization;
DROP TABLE IF EXISTS Prescription;
DROP TABLE IF EXISTS Medication;

CREATE TABLE Patient (
    patient_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    date_of_birth TEXT NOT NULL,
    gender TEXT NOT NULL CHECK (gender IN ('Male', 'Female')),
    phone_number TEXT,
    email TEXT CHECK (email LIKE '%@%'),
    street TEXT NOT NULL,
    number TEXT NOT NULL,
    floor TEXT,
    zip_code TEXT NOT NULL,
    city TEXT NOT NULL,
    emergency_contact TEXT
);

CREATE TABLE Doctor (
    doctor_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    specialty TEXT NOT NULL,
    phone_number TEXT NOT NULL,
    email TEXT CHECK (email LIKE '%@%')
);

CREATE TABLE Hospitalization (
    hospitalization_id INTEGER PRIMARY KEY,
    patient_int INTEGER NOT NULL,
    doctor_resp INTEGER NOT NULL,
    room_number INTEGER NOT NULL CHECK (room_number BETWEEN 1 AND 40),
    admission_date TEXT NOT NULL,
    discharge_date TEXT CHECK (discharge_date >= admission_date),
    FOREIGN KEY (patient_int) REFERENCES Patient(patient_id),
    FOREIGN KEY (doctor_resp) REFERENCES Doctor(doctor_id)
);

CREATE TABLE Medication (
    medication_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    type TEXT
);

CREATE TABLE Prescription (
    prescription_id INTEGER PRIMARY KEY,
    patient_presc INTEGER NOT NULL,
    doctor_presc INTEGER NOT NULL,
    medication_id INTEGER NOT NULL,
    quantity REAL NOT NULL CHECK (quantity > 0),
    FOREIGN KEY (patient_presc) REFERENCES Patient(patient_id),
    FOREIGN KEY (doctor_presc) REFERENCES Doctor(doctor_id),
    FOREIGN KEY (medication_id) REFERENCES Medication(medication_id)
);


