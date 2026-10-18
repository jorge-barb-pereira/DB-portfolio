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
CREATE OR REPLACE FUNCTION eleicoes.compute_dhondt(
    p_territorio_codigo VARCHAR(6),
    p_orgao VARCHAR(2),
    p_total_mandates INTEGER
) RETURNS TABLE (
    partido_sigla VARCHAR(50),
    computed_mandates INTEGER
) AS $$
BEGIN
    RETURN QUERY
    WITH dividers AS (
        SELECT generate_series(1, p_total_mandates) AS divisor
    ),
    quotients AS (
        SELECT 
            r.partido_sigla, 
            r.votos,
            (r.votos::numeric / d.divisor) AS quotient
        FROM eleicoes.resultados_partidos r
        CROSS JOIN dividers d
        WHERE r.territorio_codigo = p_territorio_codigo
          AND r.orgao = p_orgao
          AND r.votos > 0
    ),
    top_allocations AS (
        SELECT 
            q.partido_sigla
        FROM quotients q
        -- Rule: Order by quotient DESC. On ties, order by total votes DESC.
        ORDER BY q.quotient DESC, q.votos DESC 
        LIMIT p_total_mandates
    )
    SELECT 
        ta.partido_sigla, 
        COUNT(*)::INTEGER AS computed_mandates
    FROM top_allocations ta
    GROUP BY ta.partido_sigla;
END;
$$ LANGUAGE plpgsql;
