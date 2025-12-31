import sqlite3
from clinvar_query.modules.setup_results import create_database
from clinvar_query.utils.paths import database_file


def test_create_database_tables():
    """
    Test that create_database creates required tables
    in the configured database path.
    """
    create_database(database_file) 

    conn = sqlite3.connect(database_file)
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


