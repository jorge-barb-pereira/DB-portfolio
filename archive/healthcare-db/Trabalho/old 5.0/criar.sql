DROP TABLE IF EXISTS Hospitalization;

DROP TABLE IF EXISTS Prescription;

DROP TABLE IF EXISTS Medication;

DROP TABLE IF EXISTS Patient;

DROP TABLE IF EXISTS Doctor;

CREATE TABLE Patient (
    patient_id        INTEGER PRIMARY KEY,
    name              TEXT    NOT NULL,
    date_of_birth     TEXT    NOT NULL,
    gender            TEXT    NOT NULL
                              CHECK (gender IN ('Male', 'Female') ),
    phone_number      INTEGER    NOT NULL
                              CHECK (typeof(phone_number) = 'integer')
				CHECK(phone_number >= 100000000)
				CHECK(phone_number <= 999999999),
    email             TEXT    CHECK (email LIKE '%@%'),
    street            TEXT    ,
    number            TEXT    ,
    floor             TEXT,
    zip_code          TEXT    ,
    city              TEXT    ,
    emergency_contact INTEGER                               CHECK (typeof(emergency_contact) = 'integer')
				CHECK(emergency_contact >= 100000000)
				CHECK(emergency_contact <= 999999999)
);

CREATE TABLE Doctor (
    doctor_id    INTEGER PRIMARY KEY,
    name         TEXT    NOT NULL,
    specialty    TEXT    NOT NULL,
    phone_number INTEGER    NOT NULL
                             CHECK (typeof(phone_number) = 'integer')
				CHECK(phone_number >= 100000000)
				CHECK(phone_number <= 999999999),
    email        TEXT NOT NULL   CHECK (email LIKE '%@%') 
);

CREATE TABLE Hospitalization (
    hospitalization_id INTEGER PRIMARY KEY,
    patient_int        INTEGER NOT NULL,
    doctor_resp        INTEGER NOT NULL,
    room_number        INTEGER NOT NULL
                               CHECK (room_number BETWEEN 1 AND 40),
    admission_date     TEXT    NOT NULL,
    discharge_date     TEXT    CHECK (discharge_date >= admission_date),
    FOREIGN KEY (
        patient_int
    )
    REFERENCES Patient (patient_id),
    FOREIGN KEY (
        doctor_resp
    )
    REFERENCES Doctor (doctor_id) 
);

CREATE TABLE Medication (
    medication_id INTEGER PRIMARY KEY,
    name          TEXT    NOT NULL,
    type          TEXT
);

CREATE TABLE Prescription (
    prescription_id INTEGER PRIMARY KEY,
    patient_presc   INTEGER NOT NULL,
    doctor_presc    INTEGER NOT NULL,
    medication_id   INTEGER NOT NULL,
    quantity        INTEGER NOT NULL
                            CHECK (quantity > 0)
                            CHECK (typeof(quantity) = 'integer'),
    FOREIGN KEY (
        patient_presc
    )
    REFERENCES Patient (patient_id),
    FOREIGN KEY (
        doctor_presc
    )
    REFERENCES Doctor (doctor_id),
    FOREIGN KEY (
        medication_id
    )
    REFERENCES Medication (medication_id) 
);
