import os
import sqlite3
import pytest
from clinvar_query.modules.setup_results import create_database

TEST_DB_PATH = "tests/test_db/test_clinvar.db"


@pytest.fixture
def setup_test_db():
    os.makedirs(os.path.dirname(TEST_DB_PATH), exist_ok=True)

    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)

    create_database(TEST_DB_PATH)

    yield TEST_DB_PATH

    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)


def test_create_database_tables(setup_test_db):
    conn = sqlite3.connect(setup_test_db)
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
