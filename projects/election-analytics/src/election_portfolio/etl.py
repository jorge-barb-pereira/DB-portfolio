"""Strict normalized CSV ingestion with one transaction for the complete bundle.

No count-forcing deletions, implicit downloads, candidate imports or global resets.
Missing or malformed counts fail validation instead of silently becoming zero.
"""
import argparse
import csv
from decimal import Decimal, InvalidOperation
import json
from pathlib import Path
import re

from .db import ROOT, transaction

BODIES = {'CM','AM','AF'}
TYPES = {'Distrito','Município','Freguesia'}


def count(value):
    text = str(value).strip()
    if not re.fullmatch(r'[0-9]+',text):
        raise ValueError(f'Expected a nonnegative integer, received {text!r}')
    result = int(text)
    if result > 2147483647:
        raise ValueError('Count exceeds PostgreSQL INTEGER range')
    return result


def code(value):
    if not isinstance(value,str) or not re.fullmatch(r'[0-9]{6}',value):
        raise ValueError('Territory codes must contain exactly six digits')
    return value


def rows(path, columns):
    with path.open(encoding='utf-8-sig',newline='') as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != columns:
            raise ValueError(f'{path.name}: expected columns {columns}')
        result = list(reader)
    if not result or any(None in row or any(v is None for v in row.values()) for row in result):
        raise ValueError(f'{path.name}: empty file or malformed row')
    return result


def read_bundle(directory):
    directory = Path(directory)
    territories = rows(directory/'territories.csv',['code','name','type','parent_code','area_km2','geometry'])
    parties = rows(directory/'parties.csv',['code','name'])
    results = rows(directory/'results.csv',['territory','body','party','votes','seats'])
    statistics = rows(directory/'statistics.csv',['territory','body','registered','voters','blank','null'])
    territory_map = {}
    for row in territories:
        key = code(row['code'])
        if key in territory_map or not row['name'].strip() or row['type'] not in TYPES:
            raise ValueError('Duplicate territory or invalid territory name/type')
        try:
            area = Decimal(row['area_km2'])
        except InvalidOperation as error:
            raise ValueError('Invalid territory area') from error
        if not area.is_finite() or area < 0:
            raise ValueError('Area must be finite and nonnegative')
        row['area_km2'] = area
        if row['geometry']:
            geometry = json.loads(row['geometry'])
            if not isinstance(geometry,dict) or geometry.get('type') not in ('Polygon','MultiPolygon') or not geometry.get('coordinates'):
                raise ValueError('Geometry must be a nonempty WGS84 Polygon or MultiPolygon')
        territory_map[key] = row
    expected_parent = {'Município':'Distrito','Freguesia':'Município'}
    for row in territories:
        parent = row['parent_code']
        if row['type']=='Distrito':
            if parent:
                raise ValueError('Districts must not have a parent')
        elif parent not in territory_map or territory_map[parent]['type'] != expected_parent[row['type']]:
            raise ValueError('Invalid or missing territory parent')
    party_codes = {row['code'] for row in parties}
    if len(party_codes) != len(parties) or any(not r['code'] or len(r['code'])>50 or not r['name'].strip() for r in parties):
        raise ValueError('Duplicate or invalid party')
    stat_map = {}
    for row in statistics:
        key = (code(row['territory']),row['body'])
        if key in stat_map or key[0] not in territory_map or key[1] not in BODIES:
            raise ValueError('Duplicate statistics or unknown territory/body')
        required_type = 'Freguesia' if key[1]=='AF' else 'Município'
        if territory_map[key[0]]['type'] != required_type:
            raise ValueError('Election body does not match territory type')
        for name in ('registered','voters','blank','null'):
            row[name] = count(row[name])
        if row['voters']>row['registered'] or row['blank']+row['null']>row['voters']:
            raise ValueError('Inconsistent turnout statistics')
        stat_map[key] = row
    seen, vote_totals = set(), {key:0 for key in stat_map}
    for row in results:
        key = (code(row['territory']),row['body'],row['party'])
        if key in seen or key[:2] not in stat_map or key[2] not in party_codes:
            raise ValueError('Duplicate result or unknown election/party')
        seen.add(key)
        row['votes'],row['seats'] = count(row['votes']),count(row['seats'])
        vote_totals[key[:2]] += row['votes']
    for key,row in stat_map.items():
        if vote_totals[key] != row['voters']-row['blank']-row['null']:
            raise ValueError(f'Vote totals do not reconcile for {key}')
    territories.sort(key=lambda r:('Distrito','Município','Freguesia').index(r['type']))
    return {'territories':territories,'parties':parties,'results':results,'statistics':statistics}


def initialize_database():
    """Create schema once; refuse to overwrite an existing operational schema."""
    with transaction() as connection, connection.cursor() as cursor:
        cursor.execute("SELECT to_regnamespace('eleicoes'),to_regnamespace('dw')")
        if any(value is not None for value in cursor.fetchone()):
            raise ValueError('Schema eleicoes or dw already exists; initialization will not overwrite it')
        for path in sorted((ROOT/'sql').glob('*.sql')):
            if path.name.startswith(('01_','02_','03_','04_','06_')):
                cursor.execute(path.read_text(encoding='utf-8-sig'))


def load_bundle(directory):
    bundle = read_bundle(directory)
    with transaction() as connection, connection.cursor() as cursor:
        # Serialize application imports and warehouse refreshes within this transaction.
        cursor.execute('SELECT pg_advisory_xact_lock(20261018)')
        for row in bundle['territories']:
            cursor.execute('''INSERT INTO eleicoes.territorios(codigo,nome,tipo,parent_codigo,area_km2,geom)
                VALUES (%s,%s,%s,%s,%s,CASE WHEN %s IS NULL THEN NULL ELSE
                    ST_Multi(ST_Transform(ST_SetSRID(ST_GeomFromGeoJSON(%s::text),4326),3763)) END)
                ON CONFLICT(codigo) DO UPDATE SET nome=EXCLUDED.nome,tipo=EXCLUDED.tipo,
                    parent_codigo=EXCLUDED.parent_codigo,area_km2=EXCLUDED.area_km2,geom=EXCLUDED.geom''',
                (row['code'],row['name'],row['type'],row['parent_code'] or None,row['area_km2'],
                 row['geometry'] or None,row['geometry'] or None))
        for row in bundle['parties']:
            cursor.execute('''INSERT INTO eleicoes.partidos VALUES (%s,%s)
                ON CONFLICT(sigla) DO UPDATE SET nome_completo=EXCLUDED.nome_completo''',(row['code'],row['name']))
        for row in bundle['statistics']:
            cursor.execute('''INSERT INTO eleicoes.estatisticas_globais VALUES (%s,%s,%s,%s,%s,%s)
                ON CONFLICT(territorio_codigo,orgao) DO UPDATE SET inscritos=EXCLUDED.inscritos,
                votantes=EXCLUDED.votantes,votos_brancos=EXCLUDED.votos_brancos,votos_nulos=EXCLUDED.votos_nulos''',
                tuple(row[k] for k in ('territory','body','registered','voters','blank','null')))
        for row in bundle['results']:
            cursor.execute('''INSERT INTO eleicoes.resultados_partidos VALUES (%s,%s,%s,%s,%s)
                ON CONFLICT(territorio_codigo,orgao,partido_sigla) DO UPDATE SET votos=EXCLUDED.votos,mandatos=EXCLUDED.mandatos''',
                tuple(row[k] for k in ('territory','body','party','votes','seats')))
        for row in bundle['statistics']:
            cursor.execute('SELECT coalesce(sum(votos),0) FROM eleicoes.resultados_partidos WHERE territorio_codigo=%s AND orgao=%s',
                           (row['territory'],row['body']))
            if cursor.fetchone()[0] != row['voters']-row['blank']-row['null']:
                raise ValueError('Stored vote totals do not reconcile after merge; review obsolete result records explicitly')
        cursor.execute('CALL dw.populate_data_warehouse()')
    return {key:len(value) for key,value in bundle.items()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command',choices=('init','load','validate'))
    parser.add_argument('--directory',type=Path,default=ROOT/'examples/elections')
    args = parser.parse_args()
    try:
        if args.command=='init':
            initialize_database()
            print('Operational and warehouse schemas initialized')
        elif args.command=='load':
            print(json.dumps(load_bundle(args.directory)))
        else:
            print(json.dumps({k:len(v) for k,v in read_bundle(args.directory).items()}))
    except (ValueError,OSError) as error:
        parser.exit(2,f'Error: {error}\n')


if __name__=='__main__':
    main()
