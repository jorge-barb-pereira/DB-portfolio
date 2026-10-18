-- Int4: Quais foram os medicamentos mais prescritos e as suas respetivas quantidades totais (ordenadas de forma decrescente)?

SELECT 
    m.Name AS Medication,
    SUM(p.Quantity) AS Total_Quantity
FROM prescription p
JOIN medication m
    ON p.Medication_id = m.Medication_id
GROUP BY m.Name
ORDER BY Total_Quantity DESC;
