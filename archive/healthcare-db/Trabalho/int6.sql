-- Q6: Suspeita-se que haja uma infeção hospitalar que se transmite especificamente entre doentes hospitalizados no quarto 9. Quais os doentes que foram hospitalizados nesse quarto entre 2025-09-01 e 2025-10-01, e qual o respetivo e-mail, telefone e contacto de emergência?

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
    AND (h.admission_date <= '2025-10-01'
    AND (h.discharge_date >='2025-09-01' OR discharge_date IS NULL))  
ORDER BY h.admission_date