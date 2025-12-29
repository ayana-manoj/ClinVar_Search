# tests/test_setup_results.py
import pytest
import sqlite3
import os

from clinvar_query.modules.setup_results import create_database

# Path to a temporary test database
TEST_DB_PATH = "tests/test_db/test_clinvar.db"

@pytest.fixture(scope="function")
def setup_test_db():
    """Create a fresh test DB before each test and remove it after."""
    # Ensure the test DB folder exists
    os.makedirs(os.path.dirname(TEST_DB_PATH), exist_ok=True)
    
    # Remove old test DB if it exists
    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)
    
    # Create fresh test DB
    create_database(TEST_DB_PATH)
    
    yield TEST_DB_PATH

    # Cleanup after test
    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)


def test_create_database_tables(setup_test_db):
    """Test that all required tables are created in the test database."""
    db_path = setup_test_db
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = {row[0] for row in cursor.fetchall()}
    conn.close()

    expected_tables = {
        "patient_information",
        "variants",
        "clinvar",
    }

    missing = expected_tables - tables
    assert not missing, f"Missing tables: {missing}"
