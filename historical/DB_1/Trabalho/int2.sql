-- int2: Quais as 3 especialidades com mais doentes internados ao longo de 2025?

SELECT d.specialty,
       COUNT(p.patient_id) 
  FROM Doctor d
       JOIN
       Hospitalization h ON d.doctor_id = h.doctor_resp
       JOIN
       Patient p ON p.patient_id = h.patient_int
 WHERE (h.admission_date LIKE '2025%' OR
        h.discharge_date LIKE '2025%') 
 GROUP BY d.specialty
 ORDER BY COUNT(p.patient_id) DESC
 LIMIT 3;
