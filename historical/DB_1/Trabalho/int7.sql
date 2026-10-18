-- Q7: De forma a atribuir um prémio salarial aos médicos que foram responsáveis por mais doentes nos períodos “Jan-Apr” e “May-Aug”, quais os médicos que foram responsáveis por mais doentes?

SSELECT
    d.doctor_id,
    d.name AS Doctor_in_charge,
    d.specialty,
    h.hospitalization_id,
    h.patient_int,
    h.admission_date,
    h.discharge_date 
FROM Hospitalization h
JOIN Doctor d ON h.doctor_resp = d.doctor_id
WHERE 
    h.admission_date BETWEEN '2025-01-01' AND '2025-04-30'
ORDER BY d.name;

SELECT
    d.doctor_id,
    d.name AS Doctor_in_charge,
    d.specialty,
    h.hospitalization_id,
    h.patient_int,
    h.admission_date,
    h.discharge_date 
FROM Hospitalization h
JOIN Doctor d ON h.doctor_resp = d.doctor_id
WHERE 
    h.admission_date BETWEEN '2025-05-01' AND '2025-08-31'
ORDER BY d.name