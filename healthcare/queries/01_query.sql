-- Currently admitted patients and their rooms.
SELECT d.patient_id,
       d.Name,
       i.room_number
  FROM patient d
       JOIN
       hospitalization i ON d.patient_id = i.patient_int
 WHERE i.discharge_date IS NULL;
