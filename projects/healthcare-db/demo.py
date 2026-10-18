"""Run all seven healthcare queries against invented in-memory records."""
import json
from pathlib import Path
import sqlite3

ROOT = Path(__file__).resolve().parent


def demo_connection():
    connection = sqlite3.connect(':memory:')
    connection.row_factory = sqlite3.Row
    connection.executescript((ROOT/'schema.sql').read_text(encoding='utf-8'))
    for i in (1,2,3,7):
        connection.execute('''INSERT INTO Patient(patient_id,name,date_of_birth,gender,phone_number,email,emergency_contact)
            VALUES(?,?,?,?,?,?,?)''',(i,f'Demo Patient {i}','1980-01-01','Other',100000000+i,f'patient{i}@example.invalid',100000099))
    connection.executemany('INSERT INTO Doctor VALUES(?,?,?,?,?)',[
        (1,'Demo Doctor A','Cardiology',100000010,'doctor-a@example.invalid'),
        (2,'Demo Doctor B','Neurology',100000011,'doctor-b@example.invalid')])
    connection.executemany('INSERT INTO Medication VALUES(?,?,?)',[(1,'Demo Medicine A','Tablet'),(2,'Demo Medicine B','Liquid')])
    connection.executemany('INSERT INTO Hospitalization VALUES(?,?,?,?,?,?)',[
        (1,1,1,1,'2025-01-01','2025-02-01'),(2,3,2,2,'2025-05-10','2025-05-20'),
        (3,7,1,9,'2025-09-10','2025-09-20'),(4,2,2,3,'2025-01-01',None)])
    connection.executemany('INSERT INTO Prescription VALUES(?,?,?,?,?,?)',[
        (1,3,2,'2025-05-10',1,2),(2,3,2,'2025-05-11',2,1),(3,7,1,'2025-09-10',1,3)])
    connection.commit()
    return connection


def main():
    with demo_connection() as connection:
        output = {path.stem:[dict(row) for row in connection.execute(path.read_text(encoding='utf-8-sig'))]
                  for path in sorted((ROOT/'queries').glob('*.sql'))}
    connection.close()
    print(json.dumps(output,indent=2))


if __name__=='__main__':
    main()
