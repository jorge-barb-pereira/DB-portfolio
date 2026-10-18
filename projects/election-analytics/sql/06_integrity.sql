-- Row integrity complements bundle-level reconciliation in the ETL.
ALTER TABLE eleicoes.territorios
    ADD CHECK(codigo ~ '^[0-9]{6}$'),
    ADD CHECK(parent_codigo IS DISTINCT FROM codigo),
    ADD CHECK(area_km2 IS NULL OR area_km2>=0),
    ADD CHECK(geom IS NULL OR (NOT ST_IsEmpty(geom) AND ST_IsValid(geom)));
ALTER TABLE eleicoes.estatisticas_globais
    ADD CHECK(inscritos>=0 AND votantes>=0 AND votos_brancos>=0 AND votos_nulos>=0);
ALTER TABLE eleicoes.resultados_partidos
    ADD CHECK(votos>=0 AND mandatos>=0),
    ADD FOREIGN KEY(territorio_codigo,orgao)
        REFERENCES eleicoes.estatisticas_globais(territorio_codigo,orgao);

CREATE FUNCTION eleicoes.validate_territory_hierarchy() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE parent_type text;
BEGIN
    IF NEW.tipo='Distrito' THEN
        IF NEW.parent_codigo IS NOT NULL THEN RAISE EXCEPTION 'District cannot have a parent'; END IF;
    ELSE
        SELECT t.tipo INTO parent_type FROM eleicoes.territorios t WHERE t.codigo=NEW.parent_codigo;
        IF parent_type IS DISTINCT FROM (CASE WHEN NEW.tipo='Município' THEN 'Distrito' ELSE 'Município' END) THEN
            RAISE EXCEPTION 'Invalid territory hierarchy';
        END IF;
    END IF;
    IF EXISTS(SELECT 1 FROM eleicoes.territorios child WHERE child.parent_codigo=NEW.codigo
        AND NOT ((NEW.tipo='Distrito' AND child.tipo='Município') OR
                 (NEW.tipo='Município' AND child.tipo='Freguesia'))) THEN
        RAISE EXCEPTION 'Territory type conflicts with existing children';
    END IF;
    RETURN NEW;
END;
$$;
CREATE TRIGGER validate_territory_hierarchy BEFORE INSERT OR UPDATE ON eleicoes.territorios
    FOR EACH ROW EXECUTE FUNCTION eleicoes.validate_territory_hierarchy();

CREATE FUNCTION eleicoes.validate_body_type() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE territory_type text;
BEGIN
    SELECT t.tipo INTO territory_type FROM eleicoes.territorios t WHERE t.codigo=NEW.territorio_codigo;
    IF territory_type IS DISTINCT FROM (CASE WHEN NEW.orgao='AF' THEN 'Freguesia' ELSE 'Município' END) THEN
        RAISE EXCEPTION 'Elected body does not match territory type';
    END IF;
    RETURN NEW;
END;
$$;
CREATE TRIGGER validate_body_type BEFORE INSERT OR UPDATE ON eleicoes.estatisticas_globais
    FOR EACH ROW EXECUTE FUNCTION eleicoes.validate_body_type();
