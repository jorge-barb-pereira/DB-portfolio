-- Medication, type and quantity prescribed to demo patient 3, newest first.
SELECT m.Name AS Medication_Name,
       m.type AS Medication_Type,
       p.quantity as Quantity_Prescribed,
       p.Date_Presc AS Prescription_Date
  FROM prescription p
       JOIN
       medication m ON p.medication_id = m.medication_id
 WHERE p.Patient_Presc = 3
 ORDER BY p.Date_Presc DESC;
