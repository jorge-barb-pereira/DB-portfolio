"""Real PostgreSQL/PostGIS checks; enabled explicitly against a fresh test DB."""
import os
import csv
from pathlib import Path
import shutil
import tempfile
import unittest
import psycopg2

from election_portfolio.db import ROOT,transaction
from election_portfolio.etl import initialize_database,load_bundle
from election_portfolio.web import create_app


@unittest.skipUnless(os.getenv('RUN_DB_TESTS')=='1','Set RUN_DB_TESTS=1 for a dedicated PostgreSQL/PostGIS database')
class PostgresTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        initialize_database()
        load_bundle(ROOT/'examples/elections')

    def test_dhondt_portuguese_quotient_tie_rule(self):
        with transaction() as conn,conn.cursor() as cur:
            cur.execute("SELECT * FROM eleicoes.compute_dhondt('990100','CM',5)")
            self.assertEqual(dict(cur.fetchall()),{'LIST_A':2,'LIST_B':2,'LIST_C':1})

    def test_identical_vote_boundary_tie_is_not_arbitrarily_resolved(self):
        with self.assertRaisesRegex(psycopg2.Error,'external adjudication'):
            with transaction() as conn,conn.cursor() as cur:
                cur.execute("UPDATE eleicoes.resultados_partidos SET votos=100 WHERE territorio_codigo='990100' AND orgao='CM'")
                cur.execute("SELECT * FROM eleicoes.compute_dhondt('990100','CM',1)")

    def test_negative_counts_rejected_by_database(self):
        with self.assertRaises(psycopg2.Error):
            with transaction() as conn,conn.cursor() as cur:
                cur.execute("UPDATE eleicoes.resultados_partidos SET votos=-1 WHERE territorio_codigo='990100'")

    def test_repeat_import_is_idempotent(self):
        load_bundle(ROOT/'examples/elections')
        with transaction() as conn,conn.cursor() as cur:
            cur.execute('SELECT count(*) FROM eleicoes.resultados_partidos')
            self.assertEqual(cur.fetchone()[0],18)
            cur.execute('SELECT count(*) FROM dw.fato_resultados')
            self.assertEqual(cur.fetchone()[0],18)

    def test_warehouse_refresh_removes_stale_facts(self):
        with transaction() as conn,conn.cursor() as cur:
            try:
                cur.execute("DELETE FROM eleicoes.resultados_partidos WHERE territorio_codigo='990100' AND orgao='CM' AND partido_sigla='LIST_C'")
                cur.execute('CALL dw.populate_data_warehouse()')
                cur.execute('SELECT count(*) FROM dw.fato_resultados')
                self.assertEqual(cur.fetchone()[0],17)
            finally: conn.rollback()

    def test_audit_records_changed_values(self):
        with transaction() as conn,conn.cursor() as cur:
            try:
                cur.execute("UPDATE eleicoes.resultados_partidos SET votos=361 WHERE territorio_codigo='990100' AND orgao='CM' AND partido_sigla='LIST_A'")
                cur.execute('SELECT old_votos,new_votos FROM eleicoes.audit_resultados_partidos ORDER BY audit_id DESC LIMIT 1')
                self.assertEqual(cur.fetchone(),(360,361))
            finally: conn.rollback()

    def test_postgis_geojson_and_api_totals(self):
        client=create_app().test_client()
        response=client.get('/api/map?orgao=CM')
        self.assertEqual(response.status_code,200)
        self.assertEqual(len(response.json['features']),2)
        coords=response.json['features'][0]['geometry']['coordinates']
        self.assertTrue(coords)
        result=client.get('/api/results?orgao=CM')
        self.assertEqual(result.status_code,200)
        self.assertEqual(result.json['stats']['inscritos'],2000)
        self.assertEqual(result.json['summary']['total_votes'],1440)
        self.assertTrue(result.json['summary']['tied'])
        self.assertEqual(client.get('/api/results?codigo=999999').status_code,404)

    def test_all_analytical_queries_execute(self):
        with transaction() as conn,conn.cursor() as cur:
            cur.execute((ROOT/'sql/05_analytical_queries.sql').read_text(encoding='utf-8'))

    def test_failed_geometry_import_rolls_back_earlier_updates(self):
        with tempfile.TemporaryDirectory() as directory:
            dest=Path(directory)/'bundle'
            shutil.copytree(ROOT/'examples/elections',dest)
            path=dest/'territories.csv'
            with path.open(encoding='utf-8',newline='') as f:
                reader=csv.DictReader(f);fields=reader.fieldnames;data=list(reader)
            data[0]['name']='Temporary failed import'
            data[2]['geometry']='{"type":"Polygon","coordinates":[[[0,0],[1,1],[1,0],[0,1],[0,0]]]}'
            with path.open('w',encoding='utf-8',newline='') as f:
                writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader();writer.writerows(data)
            with self.assertRaises(psycopg2.Error): load_bundle(dest)
        with transaction() as conn,conn.cursor() as cur:
            cur.execute("SELECT nome FROM eleicoes.territorios WHERE codigo='990000'")
            self.assertEqual(cur.fetchone()[0],'Demo District')


if __name__=='__main__': unittest.main()
