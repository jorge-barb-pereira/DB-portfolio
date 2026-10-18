-- ==============================================================================
-- 05_analytical_queries.sql
--
-- DESCRIPTION:
-- Advanced analytical SQL queries for the Autárquicas 2021 database.
-- This file satisfies the analytical SQL assignment requirements:
--   1) D'Hondt validation query
--   2) 3+ window-function queries
--   3) 1 GROUP BY ROLLUP query
--   4) 1 GROUP BY CUBE query
--   5) 1 advanced aggregate query
-- ===============================================================================

SET search_path TO eleicoes, dw, public;

-- ==============================================================================
-- 0. D'HONDT VALIDATION QUERY
-- Compares stored mandates against mandates recomputed with eleicoes.compute_dhondt.
-- Change territorio_codigo/orgao if you want to test a different race.
-- ===============================================================================
WITH total_mandates AS (
    SELECT
        territorio_codigo,
        orgao,
        SUM(mandatos) AS total_mandates
    FROM eleicoes.resultados_partidos
    WHERE territorio_codigo = '110600'  -- Lisboa municipality, if present in data
      AND orgao = 'CM'
    GROUP BY territorio_codigo, orgao
), computed AS (
    SELECT
        tm.territorio_codigo,
        tm.orgao,
        d.partido_sigla,
        d.computed_mandates
    FROM total_mandates tm
    CROSS JOIN LATERAL eleicoes.compute_dhondt(
        tm.territorio_codigo,
        tm.orgao,
        tm.total_mandates::integer
    ) d
)
SELECT
    r.territorio_codigo,
    t.nome AS territorio_nome,
    r.orgao,
    r.partido_sigla,
    r.votos,
    r.mandatos AS official_mandates,
    COALESCE(c.computed_mandates, 0) AS computed_mandates,
    r.mandatos - COALESCE(c.computed_mandates, 0) AS mandate_difference
FROM eleicoes.resultados_partidos r
JOIN eleicoes.territorios t
    ON t.codigo = r.territorio_codigo
LEFT JOIN computed c
    ON c.territorio_codigo = r.territorio_codigo
   AND c.orgao = r.orgao
   AND c.partido_sigla = r.partido_sigla
WHERE r.territorio_codigo = '110600'
  AND r.orgao = 'CM'
ORDER BY r.votos DESC;


-- ==============================================================================
-- 1. WINDOW QUERY: PARTY RANKING INSIDE EACH TERRITORY/ORGAN
-- Ranks parties by votes in each local race.
-- Uses RANK() so electoral ties are preserved correctly.
-- ===============================================================================
SELECT
    r.territorio_codigo,
    t.nome AS territorio_nome,
    t.tipo AS territorio_tipo,
    r.orgao,
    r.partido_sigla,
    r.votos,
    r.mandatos,
    RANK() OVER (
        PARTITION BY r.territorio_codigo, r.orgao
        ORDER BY r.votos DESC
    ) AS party_rank,
    ROUND(
        100.0 * r.votos / NULLIF(SUM(r.votos) OVER (
            PARTITION BY r.territorio_codigo, r.orgao
        ), 0),
        2
    ) AS vote_share_perc
FROM eleicoes.resultados_partidos r
JOIN eleicoes.territorios t
    ON t.codigo = r.territorio_codigo
ORDER BY r.territorio_codigo, r.orgao, party_rank, r.partido_sigla;


-- ==============================================================================
-- 2. WINDOW QUERY: TURNOUT RANKING BY TERRITORY TYPE AND ORGAN
-- Shows which municipalities/parishes had the highest participation rates.
-- ===============================================================================
SELECT
    territorio_codigo,
    territorio_nome,
    territorio_tipo,
    orgao,
    inscritos,
    votantes,
    taxa_participacao_perc,
    RANK() OVER (
        PARTITION BY territorio_tipo, orgao
        ORDER BY taxa_participacao_perc DESC
    ) AS turnout_rank_within_type,
    AVG(taxa_participacao_perc) OVER (
        PARTITION BY territorio_tipo, orgao
    ) AS average_turnout_for_type
FROM eleicoes.vw_turnout_computation
WHERE inscritos > 0
ORDER BY territorio_tipo, orgao, turnout_rank_within_type;


-- ==============================================================================
-- 3. WINDOW QUERY: PARTY PERFORMANCE BY DISTRICT USING THE DATA WAREHOUSE
-- Aggregates results by district, then ranks each party within each district.
-- ===============================================================================
WITH party_district_totals AS (
    SELECT
        dt.codigo_distrito,
        dt.nome_distrito,
        dp.sigla AS partido_sigla,
        doo.orgao_codigo AS orgao,
        SUM(fr.votos) AS total_votos,
        SUM(fr.mandatos) AS total_mandatos
    FROM dw.fato_resultados fr
    JOIN dw.dim_territorio dt
        ON dt.sk_territorio = fr.sk_territorio
    JOIN dw.dim_partido dp
        ON dp.sk_partido = fr.sk_partido
    JOIN dw.dim_orgao doo
        ON doo.sk_orgao = fr.sk_orgao
    WHERE dt.codigo_distrito IS NOT NULL
    GROUP BY dt.codigo_distrito, dt.nome_distrito, dp.sigla, doo.orgao_codigo
)
SELECT
    codigo_distrito,
    nome_distrito,
    orgao,
    partido_sigla,
    total_votos,
    total_mandatos,
    RANK() OVER (
        PARTITION BY codigo_distrito, orgao
        ORDER BY total_votos DESC
    ) AS rank_in_district,
    ROUND(
        100.0 * total_votos / NULLIF(SUM(total_votos) OVER (
            PARTITION BY codigo_distrito, orgao
        ), 0),
        2
    ) AS district_vote_share_perc
FROM party_district_totals
ORDER BY codigo_distrito, orgao, rank_in_district;


-- ==============================================================================
-- 4. WINDOW QUERY: MARGIN OF VICTORY PER TERRITORY
-- Compares the winning party against the second-place party in each race.
-- ===============================================================================
WITH ranked AS (
    SELECT
        r.territorio_codigo,
        t.nome AS territorio_nome,
        t.tipo AS territorio_tipo,
        r.orgao,
        r.partido_sigla,
        r.votos,
        RANK() OVER (
            PARTITION BY r.territorio_codigo, r.orgao
            ORDER BY r.votos DESC
        ) AS rank_in_race,
        LEAD(r.votos) OVER (
            PARTITION BY r.territorio_codigo, r.orgao
            ORDER BY r.votos DESC
        ) AS next_party_votes
    FROM eleicoes.resultados_partidos r
    JOIN eleicoes.territorios t
        ON t.codigo = r.territorio_codigo
)
SELECT
    territorio_codigo,
    territorio_nome,
    territorio_tipo,
    orgao,
    partido_sigla AS winning_party,
    votos AS winning_votes,
    COALESCE(next_party_votes, 0) AS second_place_votes,
    votos - COALESCE(next_party_votes, 0) AS victory_margin_votes,
    ROUND(
        100.0 * (votos - COALESCE(next_party_votes, 0))
        / NULLIF(votos, 0),
        2
    ) AS victory_margin_over_winner_perc
FROM ranked
WHERE rank_in_race = 1
ORDER BY victory_margin_votes DESC;


-- ==============================================================================
-- 5. GROUP BY ROLLUP: TOTAL VOTES BY ORGAN AND PARTY
-- Produces subtotals per organ and a grand total.
-- ===============================================================================
SELECT
    COALESCE(r.orgao, 'TOTAL') AS orgao,
    COALESCE(r.partido_sigla, 'TOTAL') AS partido_sigla,
    SUM(r.votos) AS total_votos,
    SUM(r.mandatos) AS total_mandatos
FROM eleicoes.resultados_partidos r
GROUP BY ROLLUP (r.orgao, r.partido_sigla)
ORDER BY r.orgao NULLS LAST, total_votos DESC;


-- ==============================================================================
-- 6. GROUP BY CUBE: MULTIDIMENSIONAL RESULTS BY TERRITORY TYPE, ORGAN, AND PARTY
-- Produces all subtotal combinations across territory type, organ, and party.
-- ===============================================================================
SELECT
    COALESCE(t.tipo, 'ALL_TERRITORY_TYPES') AS territorio_tipo,
    COALESCE(r.orgao, 'ALL_ORGANS') AS orgao,
    COALESCE(r.partido_sigla, 'ALL_PARTIES') AS partido_sigla,
    SUM(r.votos) AS total_votos,
    SUM(r.mandatos) AS total_mandatos
FROM eleicoes.resultados_partidos r
JOIN eleicoes.territorios t
    ON t.codigo = r.territorio_codigo
GROUP BY CUBE (t.tipo, r.orgao, r.partido_sigla)
ORDER BY territorio_tipo, orgao, total_votos DESC;


-- ==============================================================================
-- 7. ADVANCED AGGREGATE QUERY: JSON SUMMARY PER TERRITORY/ORGAN
-- Uses JSONB_AGG and FILTER to create compact API-ready summaries.
-- Useful for the Flask frontend.
-- ===============================================================================
SELECT
    r.territorio_codigo,
    t.nome AS territorio_nome,
    t.tipo AS territorio_tipo,
    r.orgao,
    SUM(r.votos) AS total_valid_votes,
    SUM(r.mandatos) AS total_mandates,
    SUM(r.votos) FILTER (WHERE r.partido_sigla = 'PS') AS ps_votes,
    SUM(r.votos) FILTER (WHERE r.partido_sigla IN ('PPD/PSD', 'PSD')) AS psd_votes,
    JSONB_AGG(
        JSONB_BUILD_OBJECT(
            'party', r.partido_sigla,
            'votes', r.votos,
            'mandates', r.mandatos
        )
        ORDER BY r.votos DESC
    ) AS party_results_json
FROM eleicoes.resultados_partidos r
JOIN eleicoes.territorios t
    ON t.codigo = r.territorio_codigo
GROUP BY r.territorio_codigo, t.nome, t.tipo, r.orgao
ORDER BY t.tipo, t.nome, r.orgao;


-- ==============================================================================
-- 8. ADVANCED AGGREGATE QUERY: PARTY LIST PER TERRITORY
-- Uses STRING_AGG and ARRAY_AGG to summarize the electoral offer in each race.
-- ===============================================================================
SELECT
    r.territorio_codigo,
    t.nome AS territorio_nome,
    r.orgao,
    COUNT(*) AS number_of_parties_or_coalitions,
    STRING_AGG(r.partido_sigla, ', ' ORDER BY r.votos DESC) AS parties_ordered_by_votes,
    ARRAY_AGG(r.partido_sigla ORDER BY r.votos DESC) AS party_array_ordered_by_votes
FROM eleicoes.resultados_partidos r
JOIN eleicoes.territorios t
    ON t.codigo = r.territorio_codigo
GROUP BY r.territorio_codigo, t.nome, r.orgao
ORDER BY number_of_parties_or_coalitions DESC, territorio_nome;
