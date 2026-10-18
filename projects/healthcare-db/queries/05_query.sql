-- Admission history for demo patient 7.
SELECT 
   h.hospitalization_id,
   d.name AS Doctor_in_charge,
   h.room_number,
   h.admission_date,
   h.discharge_date
   FROM Hospitalization h
   JOIN Doctor d ON h.doctor_resp = d.doctor_id
   WHERE h.patient_int = 7
   ORDER BY h.admission_date DESC
