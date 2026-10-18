-- ==============================================================================
-- 01_operational_schema.sql
-- 
-- DESCRIPTION:
-- This file defines the core, normalized operational database schema for the 
-- Autárquicas 2021 election data. It strictly adheres to the First Normal Form 
-- (1NF) by using a "Long Table" architecture for election results.
-- ==============================================================================

-- 1. Enable PostGIS for Spatial Data
-- WHY: We are working with geographical territories (CAOP data). Standard numeric 
-- fields aren't enough to calculate intersections, bounds, or distances. PostGIS 
-- adds true spatial types and functions to PostgreSQL.
CREATE EXTENSION IF NOT EXISTS postgis;

-- Create our schema to keep things isolated from the default public schema
CREATE SCHEMA IF NOT EXISTS eleicoes;

-- ==============================================================================
-- TABLE: eleicoes.territorios
-- WHY: Instead of having separate tables for Distritos, Municípios, and Freguesias 
-- with duplicate structures, we use a single hierarchical table. The CAOP codes 
-- (dtmnfr) naturally encode this hierarchy.
-- ==============================================================================
CREATE TABLE eleicoes.territorios (
    codigo VARCHAR(6) PRIMARY KEY, -- CAOP Code: 2 digits (Distrito), 4 (Município), 6 (Freguesia)
    nome TEXT NOT NULL,
    tipo VARCHAR(50) NOT NULL CHECK (tipo IN ('Distrito', 'Município', 'Freguesia')),
    parent_codigo VARCHAR(6) REFERENCES eleicoes.territorios(codigo),
    area_km2 NUMERIC(10, 2),
    -- PostGIS Geometry column. SRID 3763 is Portugal TM06 (planar coordinates in meters).
    -- Essential for accurate area and distance calculations without unit mismatches!
    geom GEOMETRY(MultiPolygon, 3763)
);

-- ==============================================================================
-- TABLE: eleicoes.partidos
-- WHY: We need a master reference list of parties and coalitions. If a party changes 
-- its name, we update it in one place, not across millions of result rows.
-- ==============================================================================
CREATE TABLE eleicoes.partidos (
    sigla VARCHAR(50) PRIMARY KEY,
    nome_completo TEXT
);

-- ==============================================================================
-- TABLE: eleicoes.estatisticas_globais
-- WHY: General voting statistics (like turnout and blank votes) are tied to a 
-- specific territory and organ being elected, NOT to a specific party.
-- ==============================================================================
CREATE TABLE eleicoes.estatisticas_globais (
    territorio_codigo VARCHAR(6) REFERENCES eleicoes.territorios(codigo),
    orgao VARCHAR(2) NOT NULL CHECK (orgao IN ('CM', 'AM', 'AF')), -- Câmara Mun., Assembleia Mun., Assembleia Freg.
    inscritos INTEGER NOT NULL DEFAULT 0,
    votantes INTEGER NOT NULL DEFAULT 0,
    votos_brancos INTEGER NOT NULL DEFAULT 0,
    votos_nulos INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (territorio_codigo, orgao),
    CHECK (votantes <= inscritos),
    CHECK (votos_brancos + votos_nulos <= votantes)
);

-- ==============================================================================
-- TABLE: eleicoes.resultados_partidos
-- WHY: This is the fix for the 1NF violation. Instead of one row per territory 
-- with 30 columns for parties, we have one row per territory, per organ, per party.
-- This makes querying "Total votes for PS nationwide" incredibly fast using a simple SUM() and GROUP BY.
-- ==============================================================================
CREATE TABLE eleicoes.resultados_partidos (
    territorio_codigo VARCHAR(6) REFERENCES eleicoes.territorios(codigo),
    orgao VARCHAR(2) NOT NULL CHECK (orgao IN ('CM', 'AM', 'AF')),
    partido_sigla VARCHAR(50) REFERENCES eleicoes.partidos(sigla),
    votos INTEGER NOT NULL DEFAULT 0,
    mandatos INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (territorio_codigo, orgao, partido_sigla)
);

-- ==============================================================================
-- INDEXES
-- WHY: Indexes act like the table of contents in a book. Without them, querying 
-- the massive `resultados_partidos` table would require PostgreSQL to scan every 
-- single row sequentially (a Full Table Scan).
-- ==============================================================================
CREATE INDEX idx_resultados_partido ON eleicoes.resultados_partidos(partido_sigla);
CREATE INDEX idx_territorios_parent ON eleicoes.territorios(parent_codigo);
CREATE INDEX idx_territorios_tipo ON eleicoes.territorios(tipo);
-- Spatial index using GIST (Generalized Search Tree) for blazing fast geographic queries
CREATE INDEX idx_territorios_geom ON eleicoes.territorios USING GIST(geom);
