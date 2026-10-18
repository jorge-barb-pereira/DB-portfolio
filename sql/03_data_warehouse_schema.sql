-- ==============================================================================
-- 03_data_warehouse_schema.sql
-- 
-- DESCRIPTION:
-- Defines the Data Warehouse (Star Schema) and the PL/pgSQL procedure 
-- to populate it from the Operational Schema.
-- ==============================================================================

CREATE SCHEMA IF NOT EXISTS dw;

-- ==============================================================================
-- DIMENSIONS
-- ==============================================================================

-- Dimension: Organ (E.g., CM, AM, AF)
CREATE TABLE IF NOT EXISTS dw.dim_orgao (
    sk_orgao SERIAL PRIMARY KEY,
    orgao_codigo VARCHAR(2) UNIQUE,
    orgao_desc VARCHAR(50)
);

INSERT INTO dw.dim_orgao (orgao_codigo, orgao_desc)
VALUES 
('CM', 'Câmara Municipal'),
('AM', 'Assembleia Municipal'),
('AF', 'Assembleia de Freguesia')
ON CONFLICT (orgao_codigo) DO NOTHING;

-- Dimension: Party
CREATE TABLE IF NOT EXISTS dw.dim_partido (
    sk_partido SERIAL PRIMARY KEY,
    sigla VARCHAR(50) UNIQUE,
    nome_completo TEXT
);

-- Dimension: Territory
-- Flattens the hierarchical CAOP data into a single row for easy analytical grouping.
CREATE TABLE IF NOT EXISTS dw.dim_territorio (
    sk_territorio SERIAL PRIMARY KEY,
    codigo VARCHAR(6) UNIQUE,
    nome TEXT,
    tipo VARCHAR(50),
    codigo_municipio VARCHAR(6),
    nome_municipio TEXT,
    codigo_distrito VARCHAR(6),
    nome_distrito TEXT
);

-- ==============================================================================
-- FACT TABLES
-- ==============================================================================

-- Fact: Party Results
CREATE TABLE IF NOT EXISTS dw.fato_resultados (
    sk_territorio INTEGER REFERENCES dw.dim_territorio(sk_territorio),
    sk_partido INTEGER REFERENCES dw.dim_partido(sk_partido),
    sk_orgao INTEGER REFERENCES dw.dim_orgao(sk_orgao),
    votos INTEGER,
    mandatos INTEGER,
    PRIMARY KEY (sk_territorio, sk_partido, sk_orgao)
);

-- Fact: Global Statistics (Turnout, blank/null votes)
-- Kept separate from results to avoid duplicating statistics per party row.
CREATE TABLE IF NOT EXISTS dw.fato_estatisticas (
    sk_territorio INTEGER REFERENCES dw.dim_territorio(sk_territorio),
    sk_orgao INTEGER REFERENCES dw.dim_orgao(sk_orgao),
    inscritos INTEGER,
    votantes INTEGER,
    votos_brancos INTEGER,
    votos_nulos INTEGER,
    PRIMARY KEY (sk_territorio, sk_orgao)
);

-- ==============================================================================
-- ETL PROCEDURE (PL/pgSQL)
-- ==============================================================================
-- Procedure to easily refresh the Data Warehouse from the Operational Schema.
CREATE OR REPLACE PROCEDURE dw.populate_data_warehouse()
LANGUAGE plpgsql
AS $$
BEGIN
    PERFORM pg_advisory_xact_lock(20261018);
    -- Refresh fact tables inside the calling transaction.
    DELETE FROM dw.fato_resultados;
    DELETE FROM dw.fato_estatisticas;
    -- 1. Populate dim_partido
    INSERT INTO dw.dim_partido (sigla, nome_completo)
    SELECT sigla, nome_completo FROM eleicoes.partidos
    ON CONFLICT (sigla) DO UPDATE SET nome_completo = EXCLUDED.nome_completo;

    -- 2. Populate dim_territorio (Flattening the hierarchy)
    INSERT INTO dw.dim_territorio (codigo, nome, tipo, codigo_municipio, nome_municipio, codigo_distrito, nome_distrito)
    WITH RECURSIVE territory_tree AS (
        SELECT 
            codigo AS origin_codigo,
            codigo,
            nome,
            tipo,
            parent_codigo
        FROM eleicoes.territorios
        
        UNION ALL
        
        SELECT 
            tt.origin_codigo,
            t.codigo,
            t.nome,
            t.tipo,
            t.parent_codigo
        FROM territory_tree tt
        JOIN eleicoes.territorios t ON tt.parent_codigo = t.codigo
    )
    SELECT 
        t.codigo,
        t.nome,
        t.tipo,
        MAX(CASE WHEN tree.tipo = 'Município' THEN tree.codigo END) as codigo_municipio,
        MAX(CASE WHEN tree.tipo = 'Município' THEN tree.nome END) as nome_municipio,
        MAX(CASE WHEN tree.tipo = 'Distrito' THEN tree.codigo END) as codigo_distrito,
        MAX(CASE WHEN tree.tipo = 'Distrito' THEN tree.nome END) as nome_distrito
    FROM eleicoes.territorios t
    LEFT JOIN territory_tree tree ON t.codigo = tree.origin_codigo
    GROUP BY t.codigo, t.nome, t.tipo
    ON CONFLICT (codigo) DO UPDATE SET
        nome = EXCLUDED.nome,
        tipo = EXCLUDED.tipo,
        codigo_municipio = EXCLUDED.codigo_municipio,
        nome_municipio = EXCLUDED.nome_municipio,
        codigo_distrito = EXCLUDED.codigo_distrito,
        nome_distrito = EXCLUDED.nome_distrito;

    -- 3. Populate fato_resultados
    INSERT INTO dw.fato_resultados (sk_territorio, sk_partido, sk_orgao, votos, mandatos)
    SELECT 
        dt.sk_territorio,
        dp.sk_partido,
        d_org.sk_orgao,
        r.votos,
        r.mandatos
    FROM eleicoes.resultados_partidos r
    JOIN dw.dim_territorio dt ON r.territorio_codigo = dt.codigo
    JOIN dw.dim_partido dp ON r.partido_sigla = dp.sigla
    JOIN dw.dim_orgao d_org ON r.orgao = d_org.orgao_codigo
    ON CONFLICT (sk_territorio, sk_partido, sk_orgao) DO UPDATE SET
        votos = EXCLUDED.votos,
        mandatos = EXCLUDED.mandatos;

    -- 4. Populate fato_estatisticas
    INSERT INTO dw.fato_estatisticas (sk_territorio, sk_orgao, inscritos, votantes, votos_brancos, votos_nulos)
    SELECT 
        dt.sk_territorio,
        d_org.sk_orgao,
        e.inscritos,
        e.votantes,
        e.votos_brancos,
        e.votos_nulos
    FROM eleicoes.estatisticas_globais e
    JOIN dw.dim_territorio dt ON e.territorio_codigo = dt.codigo
    JOIN dw.dim_orgao d_org ON e.orgao = d_org.orgao_codigo
    ON CONFLICT (sk_territorio, sk_orgao) DO UPDATE SET
        inscritos = EXCLUDED.inscritos,
        votantes = EXCLUDED.votantes,
        votos_brancos = EXCLUDED.votos_brancos,
        votos_nulos = EXCLUDED.votos_nulos;

END;
$$;
