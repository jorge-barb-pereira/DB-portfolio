-- Int6: Suspeita-se que haja uma infeção hospitalar que se transmite especificamente entre doente hospitalizados no quarto 9. Quais os doentes que foram hospitalizados nesse quarto entre 2025-09-01 e 2025-10-01 e qual a respetiva duração do internamento?

SELECT 
    p.patient_id,
    p.name AS patient_name,
    p.email as patient_email,
    p.phone_number as patiente_phone,
    p.emergency_contact as patient_emergency_phone,
    h.room_number,
    h.admission_date,
    h.discharge_date,
    JULIANDAY(COALESCE(h.discharge_date, DATE('now'))) - JULIANDAY(h.admission_date) AS duration_days
FROM 
    Hospitalization h
JOIN 
    Patient p ON h.patient_int = p.patient_id
WHERE 
    h.room_number = 9
    AND h.admission_date BETWEEN '2025-09-01' AND '2025-10-01';
