-- Int5: Qual o histórico de internamentos de um determinado doente em que conste o medico responsável, especialidade médica, quarto utilizado, data de admissão, data de alta e duração de cada internamento, ordenado por data de admissão decrescente (ex: patient_id = 7)?

SELECT
    p.Name AS Patient_Name,
    d.Name AS Doctor_Name,
    d.Specialty AS Doctor_Speciality,
    h.Room_number,
    h.Admission_Date,
    h.Discharge_Date,
    CAST(
        julianday(COALESCE(h.Discharge_Date, DATE('now'))) - julianday(h.Admission_Date)
        AS INTEGER
    ) AS Hosp_Duration_Days
FROM hospitalization h
JOIN patient p
    ON h.Patient_int = p.Patient_id
JOIN doctor d
    ON h.Doctor_Resp = d.Doctor_id
WHERE h.Patient_int = 7
ORDER BY h.Admission_Date DESC;
