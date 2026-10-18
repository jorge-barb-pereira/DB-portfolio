-- ==============================================================================
-- 04_triggers_views.sql
-- 
-- DESCRIPTION:
-- Fulfills the "Functions, PL/pgSQL, and Triggers" requirement (20% of grade).
-- Includes triggers for data consistency/auditing and views to simplify logic.
-- ==============================================================================

-- ==============================================================================
-- 1. TRIGGERS
-- ==============================================================================

-- 1.1 Validation Trigger: Prevent negative votes or mandates
-- A simple consistency check enforcing meaningful business rules.
CREATE OR REPLACE FUNCTION eleicoes.trg_func_validate_votes()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.votos < 0 THEN
        RAISE EXCEPTION 'Consistency Error: Votes cannot be negative (Attempted: %)', NEW.votos;
    END IF;
    
    IF NEW.mandatos < 0 THEN
        RAISE EXCEPTION 'Consistency Error: Mandates cannot be negative (Attempted: %)', NEW.mandatos;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_validate_votes ON eleicoes.resultados_partidos;
CREATE TRIGGER trg_validate_votes
BEFORE INSERT OR UPDATE ON eleicoes.resultados_partidos
FOR EACH ROW
EXECUTE FUNCTION eleicoes.trg_func_validate_votes();


-- 1.2 Audit Log Trigger: Track changes to election results
-- Creates a historical record if results are tampered with or updated post-election.
CREATE TABLE IF NOT EXISTS eleicoes.audit_resultados_partidos (
    audit_id SERIAL PRIMARY KEY,
    territorio_codigo VARCHAR(6),
    orgao VARCHAR(2),
    partido_sigla VARCHAR(50) REFERENCES eleicoes.partidos(sigla) ON DELETE SET NULL,
    old_votos INTEGER,
    new_votos INTEGER,
    old_mandatos INTEGER,
    new_mandatos INTEGER,
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    changed_by VARCHAR(100) DEFAULT CURRENT_USER
);

CREATE OR REPLACE FUNCTION eleicoes.trg_func_audit_resultados()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        INSERT INTO eleicoes.audit_resultados_partidos (
            territorio_codigo, orgao, partido_sigla, 
            old_votos, new_votos, old_mandatos, new_mandatos
        ) VALUES (
            NEW.territorio_codigo, NEW.orgao, NEW.partido_sigla,
            NULL, NEW.votos, NULL, NEW.mandatos
        );
        RETURN NEW;
    ELSIF TG_OP = 'UPDATE' THEN
        -- Only log if values actually changed
        IF OLD.votos IS DISTINCT FROM NEW.votos OR OLD.mandatos IS DISTINCT FROM NEW.mandatos THEN
            INSERT INTO eleicoes.audit_resultados_partidos (
                territorio_codigo, orgao, partido_sigla, 
                old_votos, new_votos, old_mandatos, new_mandatos
            ) VALUES (
                OLD.territorio_codigo, OLD.orgao, OLD.partido_sigla,
                OLD.votos, NEW.votos, OLD.mandatos, NEW.mandatos
            );
        END IF;
        RETURN NEW;
    ELSIF TG_OP = 'DELETE' THEN
        INSERT INTO eleicoes.audit_resultados_partidos (
            territorio_codigo, orgao, partido_sigla, 
            old_votos, new_votos, old_mandatos, new_mandatos
        ) VALUES (
            OLD.territorio_codigo, OLD.orgao, OLD.partido_sigla,
            OLD.votos, NULL, OLD.mandatos, NULL
        );
        RETURN OLD;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_audit_resultados ON eleicoes.resultados_partidos;
CREATE TRIGGER trg_audit_resultados
AFTER INSERT OR UPDATE OR DELETE ON eleicoes.resultados_partidos
FOR EACH ROW
EXECUTE FUNCTION eleicoes.trg_func_audit_resultados();


-- ==============================================================================
-- 2. VIEWS
-- ==============================================================================

-- 2.1 View: Turnout Computation
-- Simplifies the logic for calculating abstention and turnout rates per territory.
CREATE OR REPLACE VIEW eleicoes.vw_turnout_computation AS
SELECT 
    t.codigo AS territorio_codigo,
    t.nome AS territorio_nome,
    t.tipo AS territorio_tipo,
    e.orgao,
    e.inscritos,
    e.votantes,
    (e.inscritos - e.votantes) AS abstencoes,
    ROUND((e.votantes::numeric / NULLIF(e.inscritos, 0)) * 100, 2) AS taxa_participacao_perc,
    ROUND(((e.inscritos - e.votantes)::numeric / NULLIF(e.inscritos, 0)) * 100, 2) AS taxa_abstencao_perc
FROM eleicoes.estatisticas_globais e
JOIN eleicoes.territorios t ON e.territorio_codigo = t.codigo;


-- 2.2 View: Vote Share Computation
-- Calculates the percentage of votes each party received relative to the total valid votes.
CREATE OR REPLACE VIEW eleicoes.vw_vote_share_computation AS
WITH TotalVotes AS (
    SELECT 
        territorio_codigo, 
        orgao, 
        SUM(votos) AS total_valid_votes
    FROM eleicoes.resultados_partidos
    GROUP BY territorio_codigo, orgao
)
SELECT 
    r.territorio_codigo,
    t.nome AS territorio_nome,
    r.orgao,
    r.partido_sigla,
    r.votos,
    r.mandatos,
    tv.total_valid_votes,
    ROUND((r.votos::numeric / NULLIF(tv.total_valid_votes, 0)) * 100, 2) AS vote_share_perc
FROM eleicoes.resultados_partidos r
JOIN TotalVotes tv ON r.territorio_codigo = tv.territorio_codigo AND r.orgao = tv.orgao
JOIN eleicoes.territorios t ON r.territorio_codigo = t.codigo;


-- 2.3 View: Winning Party Per Territory
-- Uses a window function to find the party that won each election.
CREATE OR REPLACE VIEW eleicoes.vw_winning_party_per_territory AS
WITH RankedParties AS (
    SELECT 
        territorio_codigo,
        orgao,
        partido_sigla,
        votos,
        mandatos,
        RANK() OVER (PARTITION BY territorio_codigo, orgao ORDER BY votos DESC) as rank
    FROM eleicoes.resultados_partidos
)
SELECT 
    r.territorio_codigo,
    t.nome AS territorio_nome,
    r.orgao,
    r.partido_sigla AS winning_party,
    r.votos AS winning_votes,
    r.mandatos AS winning_mandates
FROM RankedParties r
JOIN eleicoes.territorios t ON r.territorio_codigo = t.codigo
WHERE r.rank = 1;
