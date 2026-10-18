-- ==============================================================================
-- 02_functions_triggers.sql
-- 
-- DESCRIPTION:
-- Contains PL/pgSQL routines and the D'Hondt algorithm implementation.
-- ==============================================================================

-- ==============================================================================
-- 1. Table for Local Coalitions
-- ==============================================================================
CREATE TABLE IF NOT EXISTS eleicoes.coligacoes_locais (
    territorio_codigo VARCHAR(6) REFERENCES eleicoes.territorios(codigo),
    orgao VARCHAR(2) NOT NULL CHECK (orgao IN ('CM', 'AM', 'AF')),
    letra VARCHAR(10) NOT NULL, -- e.g., '[A]'
    sigla_verdadeira VARCHAR(255) NOT NULL,
    denominacao VARCHAR(255),
    PRIMARY KEY (territorio_codigo, orgao, letra)
);

CREATE TABLE IF NOT EXISTS eleicoes.candidatos (
    id SERIAL PRIMARY KEY,
    territorio_codigo VARCHAR(6) REFERENCES eleicoes.territorios(codigo),
    orgao VARCHAR(2) NOT NULL CHECK (orgao IN ('CM', 'AM', 'AF')),
    partido_sigla VARCHAR(50) REFERENCES eleicoes.partidos(sigla),
    nome TEXT NOT NULL
);

-- ==============================================================================
-- 2. D'Hondt Method Implementation (PL/pgSQL Function)
-- WHY: This allows us to recalculate mandates dynamically from votes, meeting
-- the advanced analytical SQL requirement.
-- ==============================================================================
-- Final-seat quotient ties favor the list with fewer total votes (CNE).
-- Identical-vote ties at the boundary require external adjudication.
CREATE OR REPLACE FUNCTION eleicoes.compute_dhondt(p_territorio_codigo varchar(6),
    p_orgao varchar(2),p_total_mandates integer)
RETURNS TABLE(partido_sigla varchar(50),computed_mandates integer)
LANGUAGE plpgsql AS $$
BEGIN
    IF p_total_mandates IS NULL OR p_total_mandates < 0 OR p_total_mandates > 1000 THEN
        RAISE EXCEPTION 'Mandates must be between zero and 1000';
    END IF;
    IF p_orgao NOT IN ('CM','AM','AF') OR p_orgao IS NULL THEN RAISE EXCEPTION 'Unknown elected body'; END IF;
    IF p_total_mandates > 0 AND NOT EXISTS (
        SELECT 1 FROM eleicoes.resultados_partidos r
        WHERE r.territorio_codigo=p_territorio_codigo AND r.orgao=p_orgao AND r.votos>0
    ) THEN RAISE EXCEPTION 'No positive votes for this election'; END IF;
    IF EXISTS (
        WITH ranked AS (
            SELECT r.votos::numeric/d.divisor AS quotient,r.votos,
                row_number() OVER(ORDER BY r.votos::numeric/d.divisor DESC,
                    r.votos ASC,r.partido_sigla) AS position
            FROM eleicoes.resultados_partidos r
            CROSS JOIN generate_series(1,p_total_mandates) AS d(divisor)
            WHERE r.territorio_codigo=p_territorio_codigo AND r.orgao=p_orgao AND r.votos>0
        )
        SELECT 1 FROM ranked a JOIN ranked b
          ON a.position=p_total_mandates AND b.position=p_total_mandates+1
         AND a.quotient=b.quotient AND a.votos=b.votos
    ) THEN RAISE EXCEPTION 'Unresolved identical-vote tie at seat boundary; external adjudication required'; END IF;
    RETURN QUERY
    WITH allocations AS (
        SELECT r.partido_sigla
        FROM eleicoes.resultados_partidos r
        CROSS JOIN generate_series(1,p_total_mandates) AS d(divisor)
        WHERE r.territorio_codigo=p_territorio_codigo AND r.orgao=p_orgao AND r.votos>0
        ORDER BY r.votos::numeric/d.divisor DESC,r.votos ASC,r.partido_sigla
        LIMIT p_total_mandates
    ), totals AS (
        SELECT a.partido_sigla,count(*)::integer AS seats FROM allocations a GROUP BY a.partido_sigla
    )
    SELECT r.partido_sigla,coalesce(t.seats,0)
    FROM eleicoes.resultados_partidos r LEFT JOIN totals t ON t.partido_sigla=r.partido_sigla
    WHERE r.territorio_codigo=p_territorio_codigo AND r.orgao=p_orgao ORDER BY r.partido_sigla;
END;
$$;
