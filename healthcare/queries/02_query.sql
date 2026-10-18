-- Top three specialties by distinct patients whose stays overlap 2025.

SELECT d.specialty,
       COUNT(DISTINCT p.patient_id) AS patients
  FROM Doctor d
       JOIN
       Hospitalization h ON d.doctor_id = h.doctor_resp
       JOIN
       Patient p ON p.patient_id = h.patient_int
 WHERE h.admission_date < '2026-01-01'
   AND (h.discharge_date IS NULL OR h.discharge_date > '2025-01-01')
 GROUP BY d.specialty
 ORDER BY patients DESC,d.specialty
 LIMIT 3;
