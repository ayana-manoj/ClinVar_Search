import sqlite3
import pytest
from clinvar_query.modules.setup_results import create_database

@pytest.fixture
def test_db(tmp_path):
    """
    Create a temporary test database using pytest's tmp_path.
    Returns the path to the DB.
    """
    db_path = tmp_path / "test_clinvar.db"
    create_database(str(db_path))
    return str(db_path)

def test_create_database_tables(test_db):
    """
    Verify that create_database creates the required tables
    in a temporary database 
    """
    conn = sqlite3.connect(test_db)
    cursor = conn.cursor()

    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = {row[0] for row in cursor.fetchall()}
    conn.close()

    expected_tables = {
        "patient_information",
        "variants",
        "clinvar",
    }

    assert expected_tables.issubset(tables), f"Missing tables: {expected_tables - tables}"
