-- Int7: De forma a atribuir um prêmios salariais aos médicos que foram responsáveis por mais doentes nos períodos “Jan-Abr” e “May-Aug”, quais os médicos que responsáveis por mais doentes? Em caso de empate dentro de um período deve-se atribuir prêmio a todos os médicos.

WITH Hospitalization_2025 AS (
    SELECT 
        doctor_resp,
        CASE 
            WHEN strftime('%m', admission_date) IN ('01','02','03','04') THEN 'Jan-Apr'
            WHEN strftime('%m', admission_date) IN ('05','06','07','08') THEN 'May-Aug'
        END AS four_month_period
    FROM Hospitalization
    WHERE strftime('%Y', admission_date) = '2025'
      AND strftime('%m', admission_date) BETWEEN '01' AND '08'  -- ignora set–dez
),
DoctorCount AS (
    SELECT 
        h.four_month_period,
        h.doctor_resp,
        d.name AS doctor_name,
        COUNT(*) AS total_hospitalizations
    FROM Hospitalization_2025 h
    JOIN Doctor d ON h.doctor_resp = d.doctor_id
    GROUP BY h.four_month_period, h.doctor_resp
),
RankedDoctors AS (
    SELECT 
        four_month_period,
        doctor_name,
        total_hospitalizations,
        RANK() OVER (PARTITION BY four_month_period ORDER BY total_hospitalizations DESC) AS rank_position
    FROM DoctorCount
)
SELECT 
    four_month_period,
    doctor_name,
    total_hospitalizations
FROM RankedDoctors
WHERE rank_position = 1
ORDER BY four_month_period, total_hospitalizations DESC;
