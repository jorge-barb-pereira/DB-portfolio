
-- DDL: Data Definition Language
DROP TABLE IF EXISTS Patient;
DROP TABLE IF EXISTS Doctor;
DROP TABLE IF EXISTS Internment;
DROP TABLE IF EXISTS Prescription;
DROP TABLE IF EXISTS Medication;

CREATE TABLE Patient (
    patient_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    date_of_birth DATE NOT NULL,
    gender TEXT NOT NULL,
    phone_number TEXT,
    email TEXT,
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
    email TEXT NOT NULL
);

CREATE TABLE Internment (
    internment_id INTEGER PRIMARY KEY,
    patient_int INTEGER NOT NULL,
    doctor_resp INTEGER NOT NULL,
    room_number INTEGER NOT NULL,
    admission_date DATE NOT NULL,
    discharge_date DATE,
    FOREIGN KEY (patient_int) REFERENCES Patient(patient_id),
    FOREIGN KEY (doctor_resp) REFERENCES Doctor(doctor_id)
);

CREATE TABLE Prescription (
    prescription_id INTEGER PRIMARY KEY,
    patient_presc INTEGER NOT NULL,
    doctor_presc INTEGER NOT NULL,
    medication_id INTEGER NOT NULL,
    quantity REAL NOT NULL,
    daily_frequency INTEGER NOT NULL,
    FOREIGN KEY (patient_presc) REFERENCES Patient(patient_id),
    FOREIGN KEY (doctor_presc) REFERENCES Doctor(doctor_id),
    FOREIGN KEY (medication_id) REFERENCES Medication(medication_id)
);

CREATE TABLE Medication (
    medication_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    type TEXT
);
