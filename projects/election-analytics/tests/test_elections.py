import csv
import os
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

from election_portfolio.db import ROOT, connection_settings
from election_portfolio.etl import count, read_bundle
from election_portfolio.web import create_app


class BundleTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.directory = Path(self.temp.name)/'bundle'
        shutil.copytree(ROOT/'examples/elections',self.directory)

    def tearDown(self):
        self.temp.cleanup()

    def edit(self,name,mutate):
        path = self.directory/name
        with path.open(encoding='utf-8',newline='') as f:
            reader = csv.DictReader(f)
            fields,values = reader.fieldnames,list(reader)
        mutate(values)
        with path.open('w',encoding='utf-8',newline='') as f:
            writer=csv.DictWriter(f,fieldnames=fields)
            writer.writeheader();writer.writerows(values)

    def test_valid_synthetic_bundle(self):
        bundle = read_bundle(self.directory)
        self.assertEqual(len(bundle['territories']),5)
        self.assertEqual(len(bundle['results']),18)
        self.assertEqual(bundle['territories'][0]['type'],'Distrito')

    def test_invalid_counts_are_not_silently_zeroed(self):
        for value in ('','-', '(P)', '1.9','-1','NaN','2147483648'):
            with self.subTest(value=value),self.assertRaises(ValueError): count(value)
        self.assertEqual(count('0'),0)

    def test_vote_totals_must_reconcile(self):
        self.edit('results.csv',lambda values: values[0].update(votes='361'))
        with self.assertRaisesRegex(ValueError,'reconcile'): read_bundle(self.directory)

    def test_duplicate_result_rejected(self):
        self.edit('results.csv',lambda values:values.append(values[0].copy()))
        with self.assertRaisesRegex(ValueError,'Duplicate'): read_bundle(self.directory)

    def test_invalid_parent_rejected(self):
        self.edit('territories.csv',lambda values:values[1].update(parent_code='990101'))
        with self.assertRaisesRegex(ValueError,'parent'): read_bundle(self.directory)

    def test_wrong_body_type_rejected(self):
        self.edit('statistics.csv',lambda values:values[0].update(body='AF'))
        with self.assertRaisesRegex(ValueError,'type'): read_bundle(self.directory)

    def test_nonfinite_area_rejected(self):
        self.edit('territories.csv',lambda values:values[0].update(area_km2='NaN'))
        with self.assertRaisesRegex(ValueError,'finite'): read_bundle(self.directory)


class WebBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.client = create_app().test_client()

    def test_dashboard_is_english_and_identifies_demo_data(self):
        response=self.client.get('/')
        self.assertEqual(response.status_code,200)
        self.assertIn(b'<html lang="en">',response.data)
        self.assertIn(b'invented territories',response.data)

    def test_invalid_input_rejected_before_database_access(self):
        for path in ('/api/results?orgao=BAD','/api/map?orgao=BAD',
                     '/api/results?codigo=1%27%20OR%201=1','/api/territories?orgao=BAD'):
            self.assertEqual(self.client.get(path).status_code,400)

    def test_database_password_is_required(self):
        with patch.dict(os.environ,{},clear=True),self.assertRaises(ValueError): connection_settings()


if __name__=='__main__': unittest.main()
