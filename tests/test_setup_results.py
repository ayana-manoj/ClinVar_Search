import unittest
import sqlite3
import os
from ClinVar_Search.modules.setup_results import create_database

class TestCreateDatabase(unittest.TestCase):

    def setUp(self):
        self.test_db = "test_clinvar.db"
        if os.path.exists(self.test_db):
            os.remove(self.test_db)

    def tearDown(self):
        if os.path.exists(self.test_db):
            os.remove(self.test_db)

    def test_create_database(self):
        create_database(db_path=self.test_db)
        conn = sqlite3.connect(self.test_db)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = {row[0] for row in cursor.fetchall()}
        conn.close()
        expected_tables = {
            "patient_information",
            "variants",
            "ClinVar",
            "variant_info",
            "annotated_results"
        }
        self.assertTrue(expected_tables.issubset(tables))
