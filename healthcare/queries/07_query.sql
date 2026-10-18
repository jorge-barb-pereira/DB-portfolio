-- Doctors with the most distinct admitted patients in each 2025 period; preserve ties.
WITH periods(label,start_date,end_date) AS (
 VALUES ('Jan-Apr','2025-01-01','2025-05-01'),('May-Aug','2025-05-01','2025-09-01')
), counts AS (
 SELECT p.label,d.doctor_id,d.name,d.specialty,count(DISTINCT h.patient_int) AS patients
 FROM periods p JOIN Hospitalization h ON h.admission_date>=p.start_date AND h.admission_date<p.end_date
 JOIN Doctor d ON d.doctor_id=h.doctor_resp
 GROUP BY p.label,d.doctor_id,d.name,d.specialty
), ranked AS (
 SELECT *,dense_rank() OVER(PARTITION BY label ORDER BY patients DESC) AS position FROM counts
)
SELECT label,doctor_id,name,specialty,patients FROM ranked WHERE position=1 ORDER BY label,doctor_id;
