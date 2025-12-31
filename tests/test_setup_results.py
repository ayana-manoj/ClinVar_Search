import os

# ✅ THIS IS THE ONE THING
os.environ["ClinVar_Search"] = os.path.abspath("tests")

import pytest
import sqlite3
from clinvar_query.modules.setup_results import create_database

TEST_DB_PATH = "tests/test_db/test_clinvar.db"


@pytest.fixture(scope="function")
def setup_test_db():
    """
    Create a fresh test database before each test
    and remove it afterwards.
    """
    # Ensure test DB directory exists
    os.makedirs(os.path.dirname(TEST_DB_PATH), exist_ok=True)

    # Remove any existing test DB
    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)

    # Create database at the EXACT path passed in
    create_database(TEST_DB_PATH)

    yield TEST_DB_PATH

    # Cleanup
    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)


def test_create_database_tables(setup_test_db):
    """
    Test that all required tables are created
    in the test database.
    """
    conn = sqlite3.connect(setup_test_db)
    cursor = conn.cursor()

    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table';"
    )
    tables = {row[0] for row in cursor.fetchall()}

    conn.close()

    expected_tables = {
        "patient_information",
        "variants",
        "clinvar",
    }

    missing = expected_tables - tables
    assert not missing, f"Missing tables: {missing}"
