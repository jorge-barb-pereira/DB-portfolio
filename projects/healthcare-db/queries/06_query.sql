-- Demo room 9 stays overlapping September 2025; synthetic contacts only.
SELECT
    p.patient_id,
    p.name,
    p.email,
    p.phone_number,
    p.emergency_contact,
    h.admission_date,
    h.discharge_date 
FROM Hospitalization h
JOIN Patient p ON p.patient_id = h.patient_int
WHERE 
    h.room_number = 9
    AND (h.admission_date < '2025-10-01'
    AND (h.discharge_date >'2025-09-01' OR discharge_date IS NULL))  
ORDER BY h.admission_date
