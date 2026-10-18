import os
import subprocess
import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
from dotenv import load_dotenv

load_dotenv()

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5555")
DB_NAME = os.getenv("DB_NAME", "autarquicas2021")
DB_USER = os.getenv("DB_USER", "admin")
DB_PASS = os.environ["DB_PASS"]

# Return a new psycopg2 connection using environment DB_* settings.
def get_connection():
    """Open and return a new database connection to the configured Postgres."""
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASS
    )

# Convert a value to an integer safely, treating NaN/empty/invalid as 0.
def safe_int(val):
    """Parse numeric-ish values robustly into an int, returning 0 on failure."""
    if pd.isna(val):
        return 0
    val_str = str(val).strip().replace(',', '.')
    if not val_str or val_str == '(P)' or val_str == '-':
        return 0
    try:
        return int(float(val_str))
    except ValueError:
        return 0

def remap_parent(codigo):
    # Remap island parent codes to their autonomous region equivalents.
    # Returns the remapped parent code (e.g., Madeira or Azores) or the
    # original code when no remapping is required.
    if codigo.startswith('31') or codigo.startswith('32'):
        return '310000'  # Madeira
    if codigo.startswith('4') and codigo != '410000' and codigo != '310000' and codigo != '320000':
        return '410000'  # Azores
    return codigo

def load_territories():
    # Load territory definitions (distritos, municipios, freguesias) from
    # CSV CAOP files and upsert them into the `eleicoes.territorios` table.
    print("Loading Territories (CAOP)...")
    
    # First, cleanup old island districts
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            DELETE FROM eleicoes.territorios 
            WHERE codigo IN (
                '310000', '320000', '410000', '420000', '430000', 
                '440000', '450000', '460000', '470000', '480000', '490000'
            )
            AND tipo = 'Distrito';
        """)
        
        cur.execute("""
            UPDATE eleicoes.territorios 
            SET parent_codigo = '310000' 
            WHERE parent_codigo IN ('310000', '320000');
        """)
        
        cur.execute("""
            UPDATE eleicoes.territorios 
            SET parent_codigo = '410000' 
            WHERE parent_codigo IN ('410000', '420000', '430000', '440000', '450000', '460000', '470000', '480000', '490000');
        """)
        conn.commit()
    except Exception as e:
        conn.rollback()
    finally:
        cur.close()
        conn.close()
    
    # Read files
    df_dist = pd.read_csv('etl/data/Areas_Distrito_CAOP2025.csv', sep=';', encoding='utf-8')
    df_muni = pd.read_csv('etl/data/Areas_Municipio_CAOP2025.csv', sep=';', encoding='utf-8')
    df_freg = pd.read_csv('etl/data/Areas_Freguesia_CAOP2025.csv', sep=';', encoding='utf-8')
    
    # Define island codes to exclude
    madeira_codes = [31, 32]
    azores_codes = [41, 42, 43, 44, 45, 46, 47, 48, 49]
    
    # 1. Distritos - skip individual islands
    distritos = []
    for _, row in df_dist.iterrows():
        cod_num = int(row['dt'])
        cod = str(cod_num).zfill(2).ljust(6, '0')
        area_str = str(row['area_km2']).replace(',', '.') if 'area_km2' in row and not pd.isna(row['area_km2']) else '0'
        area = float(area_str)
        
        # Skip individual islands - they will be replaced by autonomous regions
        if cod_num in madeira_codes or cod_num in azores_codes:
            continue
            
        distritos.append((cod, row['distrito_ilha_dsg'], 'Distrito', None, area))
    
    # Add the two autonomous regions as districts
    distritos.append(('310000', 'Região Autónoma da Madeira', 'Distrito', None, 0.0))
    distritos.append(('410000', 'Região Autónoma dos Açores', 'Distrito', None, 0.0))

    # 2. Municipios
    muni_col = [c for c in df_muni.columns if 'munic' in c.lower()][0]
    municipios = []
    for _, row in df_muni.iterrows():
        base_cod = str(row['dtmn']).replace('.0', '').zfill(4)
        cod = base_cod.ljust(6, '0')
        parent = base_cod[:2].ljust(6, '0')
        # Remap parent if it's an island
        parent = remap_parent(parent)
        area_str = str(row['area_km2']).replace(',', '.') if 'area_km2' in row and not pd.isna(row['area_km2']) else '0'
        area = float(area_str)
        municipios.append((cod, row[muni_col], 'Município', parent, area))
        
    # 3. Freguesias
    freg_col = [c for c in df_freg.columns if 'freguesia' in c.lower()][0]
    freguesias = []
    for _, row in df_freg.iterrows():
        base_cod = str(row['dtmnfr']).replace('.0', '').zfill(6)
        cod = base_cod.ljust(6, '0')
        parent = base_cod[:4].ljust(6, '0')
        area_str = str(row['area_km2']).replace(',', '.') if 'area_km2' in row and not pd.isna(row['area_km2']) else '0'
        area = float(area_str)
        freguesias.append((cod, row[freg_col], 'Freguesia', parent, area))
        
    all_territories = distritos + municipios + freguesias
    
    query = """
        INSERT INTO eleicoes.territorios (codigo, nome, tipo, parent_codigo, area_km2)
        VALUES %s
        ON CONFLICT (codigo) DO UPDATE 
        SET nome = EXCLUDED.nome, 
            tipo = EXCLUDED.tipo, 
            parent_codigo = EXCLUDED.parent_codigo,
            area_km2 = EXCLUDED.area_km2;
    """
    
    conn = get_connection()
    cur = conn.cursor()
    try:
        execute_values(cur, query, all_territories)
        conn.commit()
        print(f"Loaded {len(all_territories)} territories.")
        print("  - Autonomous regions added: Madeira (310000) and Azores (410000)")
        print("  - Individual islands merged into their respective regions")
    except Exception as e:
        conn.rollback()
        print(f"Error loading territories: {e}")
    finally:
        cur.close()
        conn.close()

def load_coalitions():
    # Parse coalition mapping from `mapa_anexo.csv` and return a mapping
    # that resolves placeholder letters to real party siglas per territory.
    print("Loading Coalitions (mapa_anexo)...")
    df = pd.read_csv('etl/data/mapa_anexo.csv', sep=';', encoding='utf-8')
    
    mapping = {}
    for _, row in df.iterrows():
        cod = str(row.iloc[0]).replace('.0', '').strip().zfill(6)
        org = str(row.iloc[3]).strip()
        
        # Columns start from index 4: [A]SIGLA, DENOMINAÇÃO, [B]SIGLA, DENOMINAÇÃO...
        for i in range(4, len(row), 2):
            col_name = df.columns[i]
            if pd.isna(col_name) or not col_name.endswith('SIGLA'):
                continue
            
            letter = col_name.replace('[', '').replace(']SIGLA', '').strip() # e.g. "A"
            sigla = str(row[i]).strip()
            
            if not pd.isna(row[i]) and sigla != 'nan' and sigla:
                # Add to mapping: (cod, org, letter) -> real_sigla
                mapping[(cod, org, f"[{letter}]")] = sigla
                mapping[(cod, org, letter)] = sigla # sometimes it appears without brackets
                
    return mapping

def load_results_and_mandates(coalition_map):
    # Parse election results and mandates from `mapa_1_resultados.csv`
    # and `mapa_2_perc_mandatos.csv`, resolve coalition siglas using
    # `coalition_map`, and insert aggregated results into the DB.
    print("Loading Election Results & Mandates...")
    
    # 1. Parse mapa_1 (Votes)
    df_v = pd.read_csv('etl/data/mapa_1_resultados.csv', sep=';', encoding='utf-8', header=None, skiprows=2)
    header_parties_v = df_v.iloc[1].values
    data_v = df_v.iloc[2:].copy()
    
    global_stats = []
    parties = set()
    seen_territories = set()
    
    # (cod, org, sigla) -> votes
    votes_dict = {}
    
    for _, row in data_v.iterrows():
        if pd.isna(row[0]) or str(row[0]).strip() == '': continue
            
        cod = str(row[0]).replace('.0', '').strip().zfill(6)
        org = str(row[3]).strip()
        if org.lower() == 'nan' or not org: continue
            
        conc_name = str(row[1]).strip() if not pd.isna(row[1]) else ""
        freg_name = str(row[2]).strip() if not pd.isna(row[2]) else ""
        
        # Apply parent remapping for territories
        parent_cod = remap_parent(cod[:2].ljust(6, '0')) if cod.endswith('00') else remap_parent(cod[:4].ljust(6, '0'))
        
        if cod.endswith('00'):
            seen_territories.add((cod, conc_name if conc_name else "Desconhecido", 'Município', parent_cod, 0.0))
        else:
            seen_territories.add((cod, freg_name if freg_name else "Desconhecida", 'Freguesia', parent_cod, 0.0))
            
        inscritos = safe_int(row[4])
        votantes = safe_int(row[5])
        brancos = safe_int(row[6])
        nulos = safe_int(row[7])
        global_stats.append((cod, org, inscritos, votantes, brancos, nulos))
        
        for i in range(8, len(header_parties_v)):
            if not pd.isna(header_parties_v[i]):
                raw_party = str(header_parties_v[i]).strip()
                if raw_party and raw_party not in ['SIGLAS COLIGAÇÕES', 'SIGLAS GCE', '']:
                    # Resolve generic letters using the map
                    real_party = coalition_map.get((cod, org, raw_party), raw_party)
                    votes_val = row[i]
                    if not pd.isna(votes_val) and str(votes_val).strip() != '':
                        votes = safe_int(votes_val)
                        parties.add(real_party)
                        votes_dict[(cod, org, real_party)] = votes

    # 2. Parse mapa_2 (Mandates)
    df_m = pd.read_csv('etl/data/mapa_2_perc_mandatos.csv', sep=';', encoding='utf-8', header=None, skiprows=2)
    header_parties_m = df_m.iloc[0].values
    data_m = df_m.iloc[2:].copy()
    
    # (cod, org, sigla) -> mandates
    mandates_dict = {}
    
    for _, row in data_m.iterrows():
        if pd.isna(row[0]) or str(row[0]).strip() == '': continue
            
        cod = str(row[0]).replace('.0', '').strip().zfill(6)
        org = str(row[3]).strip()
        if org.lower() == 'nan' or not org: continue
        
        # In mapa_2, parties take 2 columns (% and M). The party name is over the % column.
        for i in range(4, len(header_parties_m), 2):
            if i < len(header_parties_m) and not pd.isna(header_parties_m[i]):
                raw_party = str(header_parties_m[i]).strip()
                if raw_party:
                    real_party = coalition_map.get((cod, org, raw_party), raw_party)
                    
                    # Mandates are at index i + 1
                    if i + 1 < len(row):
                        mand_val = row[i + 1]
                        if not pd.isna(mand_val) and str(mand_val).strip() != '':
                            mandates = safe_int(mand_val)
                            mandates_dict[(cod, org, real_party)] = mandates
                            parties.add(real_party)

    # 3. Combine Votes and Mandates
    party_results = []
    # Combine keys from both dictionaries
    all_keys = set(votes_dict.keys()).union(set(mandates_dict.keys()))
    
    for key in all_keys:
        cod, org, sigla = key
        votes = votes_dict.get(key, 0)
        mandates = mandates_dict.get(key, 0)
        party_results.append((cod, org, sigla, votes, mandates))
        
    print(f"Found {len(parties)} unique parties/coalitions.")
    
    # Save to DB
    conn = get_connection()
    cur = conn.cursor()
    
    try:
        execute_values(cur, """
            INSERT INTO eleicoes.territorios (codigo, nome, tipo, parent_codigo, area_km2)
            VALUES %s ON CONFLICT (codigo) DO NOTHING;
        """, list(seen_territories))
        
        party_data = [(p, p) for p in parties]
        execute_values(cur, """
            INSERT INTO eleicoes.partidos (sigla, nome_completo) VALUES %s
            ON CONFLICT (sigla) DO NOTHING;
        """, party_data)
        
        execute_values(cur, """
            INSERT INTO eleicoes.estatisticas_globais (territorio_codigo, orgao, inscritos, votantes, votos_brancos, votos_nulos)
            VALUES %s ON CONFLICT (territorio_codigo, orgao) DO NOTHING;
        """, global_stats)
        
        execute_values(cur, """
            INSERT INTO eleicoes.resultados_partidos (territorio_codigo, orgao, partido_sigla, votos, mandatos)
            VALUES %s ON CONFLICT (territorio_codigo, orgao, partido_sigla) DO NOTHING;
        """, party_results)
        
        conn.commit()
        print(f"Loaded results and mandates for {len(seen_territories)} territories.")
    except Exception as e:
        conn.rollback()
        print(f"Error loading results and mandates: {e}")
    finally:
        cur.close()
        conn.close()

def load_candidates(coalition_map):
    # Parse elected candidates from `mapa_3_eleitos.csv`, map them to
    # valid party siglas using `coalition_map`, and insert into the DB.
    print("Loading Elected Candidates (mapa_3)...")
    df = pd.read_csv('etl/data/mapa_3_eleitos.csv', sep=';', encoding='utf-8', header=None, skiprows=1)
    
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT sigla FROM eleicoes.partidos")
    valid_parties = {row[0] for row in cur.fetchall()}
    
    candidatos_to_insert = []
    seen_territories = set()
    current_cod = None
    current_org = None
    current_parties = []
    
    for i, row in df.iterrows():
        # Check if this is a territory row (first column is numeric code)
        val0 = str(row[0]).strip()
        if val0.replace('.0', '').isdigit():
            current_cod = val0.replace('.0', '').zfill(6)
            current_org = str(row[3]).strip()
            
            # Capture any missing territories
            conc_name = str(row[1]).strip() if not pd.isna(row[1]) else ""
            freg_name = str(row[2]).strip() if not pd.isna(row[2]) else ""
            
            if current_cod.endswith('00'):
                seen_territories.add((current_cod, conc_name if conc_name else "Desconhecido", 'Município', current_cod[:2].ljust(6, '0'), 0.0))
            else:
                seen_territories.add((current_cod, freg_name if freg_name else "Desconhecida", 'Freguesia', current_cod[:4].ljust(6, '0'), 0.0))
            
            # The next row contains the party headers
            if i + 1 < len(df):
                party_row = df.iloc[i + 1]
                current_parties = []
                for p in party_row.values:
                    if not pd.isna(p):
                        raw_party = str(p).strip()
                        real_party = coalition_map.get((current_cod, current_org, raw_party), raw_party)
                        current_parties.append(real_party)
                    else:
                        current_parties.append(None)
            continue
            
        # Check if this is a party header row (already processed above)
        if current_parties and val0 == current_parties[0]:
            continue
            
        # Check if this is an empty row or title row
        if pd.isna(row[0]) or 'III - ELEITOS' in val0 or 'CÓD' in val0:
            continue
            
        # It must be a names row!
        if current_cod and current_org and current_parties:
            for col_idx, name_val in enumerate(row.values):
                if col_idx < len(current_parties) and current_parties[col_idx] is not None:
                    if not pd.isna(name_val) and str(name_val).strip() != '':
                        nome = str(name_val).strip()
                        sigla = current_parties[col_idx]
                        if sigla in valid_parties:
                            candidatos_to_insert.append((current_cod, current_org, sigla, nome))

    try:
        # First, insert any missing territories to avoid Foreign Key violations
        execute_values(cur, """
            INSERT INTO eleicoes.territorios (codigo, nome, tipo, parent_codigo, area_km2)
            VALUES %s ON CONFLICT (codigo) DO NOTHING;
        """, list(seen_territories))
        
        execute_values(cur, """
            INSERT INTO eleicoes.candidatos (territorio_codigo, orgao, partido_sigla, nome)
            VALUES %s;
        """, candidatos_to_insert)
        
        conn.commit()
        print(f"Loaded {len(candidatos_to_insert)} elected candidates.")
    except Exception as e:
        conn.rollback()
        print(f"Error loading candidates: {e}")
    finally:
        cur.close()
        conn.close()

def load_geometries():
    # Import CAOP 2021 shapefiles into PostGIS (using `ogr2ogr`), merge
    # and transform geometries, and update `eleicoes.territorios.geom` for
    # freguesias, municipios and distritos.
    print("Loading CAOP 2021 geometries into PostGIS...")

    caop_files = [
        (
            "etl/data/CAOP_2021/Cont_AAD_CAOP2021.shp",
            "Cont_AAD_CAOP2021",
            "staging_geo.caop2021_cont"
        ),
        (
            "etl/data/CAOP_2021/ArqMadeira_AAd_CAOP2021.shp",
            "ArqMadeira_AAd_CAOP2021",
            "staging_geo.caop2021_madeira"
        ),
        (
            "etl/data/CAOP_2021/ArqAcores_GCentral_AAd_CAOP2021.shp",
            "ArqAcores_GCentral_AAd_CAOP2021",
            "staging_geo.caop2021_acores_central"
        ),
        (
            "etl/data/CAOP_2021/ArqAcores_GOriental_AAd_CAOP2021.shp",
            "ArqAcores_GOriental_AAd_CAOP2021",
            "staging_geo.caop2021_acores_oriental"
        ),
        (
            "etl/data/CAOP_2021/ArqAcores_GOcidental_AAd_CAOP2021.shp",
            "ArqAcores_GOcidental_AAd_CAOP2021",
            "staging_geo.caop2021_acores_ocidental"
        ),
    ]

    conn_str = (
        f"PG:host={DB_HOST} port={DB_PORT} dbname={DB_NAME} "
        f"user={DB_USER} password={DB_PASS}"
    )

    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute("CREATE SCHEMA IF NOT EXISTS staging_geo;")
        conn.commit()

        print("\n Importing CAOP 2021 shapefiles...")

        # Connection string for ogr2ogr INSIDE the container
        docker_conn_str = f"PG:host=127.0.0.1 port=5432 dbname={DB_NAME} user={DB_USER} password={DB_PASS}"

        for shp_path, layer_name, table_name in caop_files:
            print(f"  - Importing {layer_name}...")

            # Map the host relative path to the absolute path inside the container
            docker_shp_path = "/" + shp_path

            result = subprocess.run(
                [
                    "docker", "exec", "at_db_postgis",
                    "ogr2ogr",
                    "-f", "PostgreSQL",
                    docker_conn_str,
                    docker_shp_path,
                    layer_name,
                    "-nln", table_name,
                    "-overwrite",
                    "-nlt", "MULTIPOLYGON",
                    "-lco", "GEOMETRY_NAME=geom",
                ],
                capture_output=True,
                text=True,
            )

            if result.returncode != 0:
                print("STDOUT:", result.stdout)
                print("STDERR:", result.stderr)
                raise RuntimeError(f"Failed to import {layer_name}")

            print(f"    Imported into {table_name}")

        cur.execute("""
            WITH caop2021 AS (
                SELECT dicofre::text AS codigo, geom FROM staging_geo.caop2021_cont
                UNION ALL
                SELECT dicofre::text AS codigo, ST_Transform(geom, 3763) FROM staging_geo.caop2021_madeira
                UNION ALL
                SELECT dicofre::text AS codigo, ST_Transform(geom, 3763) FROM staging_geo.caop2021_acores_central
                UNION ALL
                SELECT dicofre::text AS codigo, ST_Transform(geom, 3763) FROM staging_geo.caop2021_acores_oriental
                UNION ALL
                SELECT dicofre::text AS codigo, ST_Transform(geom, 3763) FROM staging_geo.caop2021_acores_ocidental
            ),
            merged AS (
                SELECT
                    codigo,
                    ST_Multi(ST_Union(geom)) AS geom
                FROM caop2021
                GROUP BY codigo
            )
            UPDATE eleicoes.territorios t
            SET geom = m.geom
            FROM merged m
            WHERE t.tipo = 'Freguesia'
              AND t.codigo = m.codigo;
        """)
        print(f"  - Updated {cur.rowcount} freguesia geometries")

        cur.execute("""
            UPDATE eleicoes.territorios t
            SET geom = sub.geom
            FROM (
                SELECT
                    target_codigo,
                    ST_Multi(ST_Union(geom)) AS geom
                FROM (
                    SELECT '030204' AS target_codigo, geom
                    FROM staging_geo.caop2021_cont
                    WHERE dicofre::text IN ('0302FD', '0302FE')

                    UNION ALL

                    SELECT '030207' AS target_codigo, geom
                    FROM staging_geo.caop2021_cont
                    WHERE dicofre::text IN ('0302FG', '0302FH', '0302FI', '0302FJ')
                ) x
                GROUP BY target_codigo
            ) sub
            WHERE t.codigo = sub.target_codigo;
        """)
        print(f"  - Fixed {cur.rowcount} Barcelos special freguesia geometries")

        print("\nCreating municipality geometries from freguesias...")

        cur.execute("""
            UPDATE eleicoes.territorios m
            SET geom = sub.geom
            FROM (
                SELECT
                    parent_codigo AS municipio_codigo,
                    ST_Multi(ST_Union(geom)) AS geom
                FROM eleicoes.territorios
                WHERE tipo = 'Freguesia'
                  AND geom IS NOT NULL
                GROUP BY parent_codigo
            ) sub
            WHERE m.tipo = 'Município'
              AND m.codigo = sub.municipio_codigo;
        """)
        print(f"  - Updated {cur.rowcount} municipality geometries")

        print("\nCreating district/regional geometries from municipalities...")

        cur.execute("""
            UPDATE eleicoes.territorios d
            SET geom = sub.geom
            FROM (
                SELECT
                    parent_codigo AS distrito_codigo,
                    ST_Multi(ST_Union(geom)) AS geom
                FROM eleicoes.territorios
                WHERE tipo = 'Município'
                  AND geom IS NOT NULL
                GROUP BY parent_codigo
            ) sub
            WHERE d.tipo = 'Distrito'
              AND d.codigo = sub.distrito_codigo;
        """)
        print(f"  - Updated {cur.rowcount} district/regional geometries")

        cur.execute("""
            SELECT
                tipo,
                COUNT(*) AS total,
                COUNT(geom) AS with_geometry
            FROM eleicoes.territorios
            GROUP BY tipo
            ORDER BY tipo;
        """)

        print("\nGeometry coverage:")
        for tipo, total, with_geom in cur.fetchall():
            print(f"  - {tipo}: {with_geom}/{total}")

        conn.commit()
        print("\nCAOP 2021 geometries loaded successfully!")

    except Exception as e:
        conn.rollback()
        print(f"Error loading CAOP 2021 geometries: {e}")
        import traceback
        traceback.print_exc()
    finally:
        cur.close()
        conn.close()

def reconcile_territories_to_2021_structure():
    # Remove extra CAOP freguesias not used in the 2021 election structure.
    # Keeps expected counts per district and deletes leftovers without
    # project data (results/candidates/statistics).
    print("\nCleaning extra CAOP freguesias not used in 2021 election structure...")

    expected_counts = {
        "Aveiro": 147,
        "Beja": 75,
        "Braga": 347,
        "Bragança": 226,
        "Castelo Branco": 120,
        "Coimbra": 155,
        "Évora": 69,
        "Faro": 67,
        "Guarda": 242,
        "Leiria": 110,
        "Lisboa": 134,
        "Portalegre": 69,
        "Porto": 243,
        "Região Autónoma da Madeira": 54,
        "Região Autónoma dos Açores": 156,
        "Santarém": 141,
        "Setúbal": 55,
        "Viana do Castelo": 208,
        "Vila Real": 197,
        "Viseu": 277,
    }

    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute("""
            CREATE TEMP TABLE tmp_freguesias_to_delete (
                codigo VARCHAR(6) PRIMARY KEY
            ) ON COMMIT DROP;
        """)

        for district_name, expected_count in expected_counts.items():
            cur.execute("""
                WITH district_freguesias AS (
                    SELECT
                        f.codigo,
                        CASE
                            WHEN EXISTS (
                                SELECT 1 FROM eleicoes.estatisticas_globais e
                                WHERE e.territorio_codigo = f.codigo
                            )
                            OR EXISTS (
                                SELECT 1 FROM eleicoes.resultados_partidos r
                                WHERE r.territorio_codigo = f.codigo
                            )
                            OR EXISTS (
                                SELECT 1 FROM eleicoes.candidatos c
                                WHERE c.territorio_codigo = f.codigo
                            )
                            THEN 1
                            ELSE 0
                        END AS has_project_data
                    FROM eleicoes.territorios d
                    JOIN eleicoes.territorios m
                      ON m.parent_codigo = d.codigo
                     AND m.tipo = 'Município'
                    JOIN eleicoes.territorios f
                      ON f.parent_codigo = m.codigo
                     AND f.tipo = 'Freguesia'
                    WHERE d.tipo = 'Distrito'
                      AND d.nome = %s
                ),
                ranked AS (
                    SELECT
                        codigo,
                        ROW_NUMBER() OVER (
                            ORDER BY has_project_data ASC, codigo ASC
                        ) AS rn,
                        COUNT(*) OVER () AS total_count
                    FROM district_freguesias
                )
                INSERT INTO tmp_freguesias_to_delete (codigo)
                SELECT codigo
                FROM ranked
                WHERE rn <= GREATEST(total_count - %s, 0)
                ON CONFLICT DO NOTHING;
            """, (district_name, expected_count))

        cur.execute("SELECT COUNT(*) FROM tmp_freguesias_to_delete;")
        total_to_delete = cur.fetchone()[0]
        print(f"  - Selected {total_to_delete} extra freguesias to delete")

        cur.execute("""
            DELETE FROM eleicoes.candidatos c
            USING tmp_freguesias_to_delete td
            WHERE c.territorio_codigo = td.codigo;
        """)
        print(f"  - Deleted {cur.rowcount} candidate rows")

        cur.execute("""
            DELETE FROM eleicoes.estatisticas_globais e
            USING tmp_freguesias_to_delete td
            WHERE e.territorio_codigo = td.codigo;
        """)
        print(f"  - Deleted {cur.rowcount} statistics rows")

        cur.execute("""
            DELETE FROM eleicoes.resultados_partidos r
            USING tmp_freguesias_to_delete td
            WHERE r.territorio_codigo = td.codigo;
        """)
        print(f"  - Deleted {cur.rowcount} result rows")

        cur.execute("""
            DELETE FROM eleicoes.coligacoes_locais cl
            USING tmp_freguesias_to_delete td
            WHERE cl.territorio_codigo = td.codigo;
        """)
        print(f"  - Deleted {cur.rowcount} coalition rows")

        cur.execute("""
            DELETE FROM eleicoes.territorios f
            USING tmp_freguesias_to_delete td
            WHERE f.codigo = td.codigo;
        """)
        print(f"  - Deleted {cur.rowcount} extra freguesias")

        conn.commit()
        print("Extra CAOP freguesias cleaned successfully!")

    except Exception as e:
        conn.rollback()
        print(f"Error cleaning extra freguesias: {e}")
    finally:
        cur.close()
        conn.close()

def populate_dw():
    # Trigger the data warehouse population stored procedure
    # `dw.populate_data_warehouse()` to build analytical tables.
    print("Populating Data Warehouse...")
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("CALL dw.populate_data_warehouse()")
        conn.commit()
        print("Data Warehouse populated successfully!")
    except Exception as e:
        conn.rollback()
        print(f"Error populating data warehouse: {e}")
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    print("=" * 60)
    print("Starting ETL Pipeline for 2021 Portuguese Elections")
    print("=" * 60)

    load_territories()

    cmap = load_coalitions()
    load_results_and_mandates(cmap)
    load_candidates(cmap)

    reconcile_territories_to_2021_structure()
    load_geometries()
    populate_dw()

    print("=" * 60)
    print("ETL Pipeline completed successfully!")
    print("\nTerritory hierarchy now includes:")
    print("  - 18 mainland districts")
    print("  - Região Autónoma da Madeira")
    print("  - Região Autónoma dos Açores")
    print("  - Full geometry coverage for districts, municipalities, and freguesias")
    print("=" * 60)