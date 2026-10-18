
-- DDL: Data Definition Language

CREATE TABLE Patient (
    patient_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    date_of_birth DATE NOT NULL,
    gender TEXT NOT NULL,
    phone_number TEXT,
    email TEXT,
    address TEXT,
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
    patient_id INTEGER NOT NULL,
    doctor_id INTEGER NOT NULL,
    room_number INTEGER NOT NULL,
    admission_date DATE NOT NULL,
    discharge_date DATE,
    FOREIGN KEY (patient_id) REFERENCES Patient(patient_id),
    FOREIGN KEY (doctor_id) REFERENCES Doctor(doctor_id)
);

CREATE TABLE Prescription (
    prescription_id INTEGER PRIMARY KEY,
    internment_id INTEGER NOT NULL,
    medication_id INTEGER NOT NULL,
    quantity REAL NOT NULL,
    daily_frequency INTEGER NOT NULL,
    FOREIGN KEY (internment_id) REFERENCES Internment(internment_id),
    FOREIGN KEY (medication_id) REFERENCES Medication(medication_id)
);

CREATE TABLE Medication (
    medication_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    type TEXT
);
