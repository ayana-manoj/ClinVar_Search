#Testing to see if all required tables are created in the database
import unittest
import sqlite3
import os
import sys

# Ensure the project root is in sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from ClinVar_Search.modules.setup_results import create_database

class TestCreateDatabase(unittest.TestCase):
    
    def setUp(self):
        """Create a temporary test database before each test."""
        self.test_db = "test_clinvar.db"
        # Remove old test database if it exists
        if os.path.exists(self.test_db):
            os.remove(self.test_db)

    def tearDown(self):
        """Remove temporary test database after each test."""
        if os.path.exists(self.test_db):
            os.remove(self.test_db)

    def test_create_database(self):
        """Test that all required tables are created in the database."""
        # Call the function
        create_database(self.test_db)

        # Connect to DB and fetch table names
        conn = sqlite3.connect(self.test_db)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = {row[0] for row in cursor.fetchall()}
        conn.close()

        # Expected tables
        expected_tables = {
            "patient_information",
            "variants",
            "ClinVar",
            "variant_info",
            "annotated_results"
        }

        # Assert all expected tables exist
        self.assertTrue(expected_tables.issubset(tables))
