-- Identificar as 3 especialidades com mais doentes internados em 2023. 

SELECT d.specialty, COUNT(p.patient_id)
FROM  Doctor d
JOIN Hospitalization h ON d.doctor_id = h.doctor_resp 
JOIN Patient p ON p.patient_id = h.patient_int
WHERE (h.admission_date LIKE '2023%' OR h.discharge_date LIKE '2023%')
GROUP BY d.specialty
ORDER BY COUNT(p.patient_id) DESC
LIMIT 3;

-- Quais foram os medicamentos mais prescritos nos últimos 30 dias? Ordenar de forma decrescente.
 
-- Identificar todos os doentes e médicos que possam ter estado em contacto direto com um doente diagnosticado com Covid, internado entre os dias 3 e 5 de outubro de 2025, no quarto número 3.

-- De forma a otimizar a distribuição de doentes, identificar os médicos que têm o maior número de pacientes internados sob a sua responsabilidade. Ordenar por número de internamentos.

-- Identificar os internamentos que tiveram duração superior a 10 dias. 

