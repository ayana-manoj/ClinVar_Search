"""
Tests for the database insertion functions in
`clinvar_query.modules.insert_annotated_results`.

These tests check that patient details, variant records and ClinVar
annotations are correctly written to a SQLite database. A temporary
database is used so that tests are isolated and repeatable.
"""

from clinvar_query.modules.insert_annotated_results import (
    insert_patient_information,
    insert_variants,
    insert_clinvar,
)
from clinvar_query.utils.logger import logger
import sqlite3
import pytest


@pytest.fixture
def temp_db(tmp_path, monkeypatch):
    """
    Set up a temporary SQLite database for testing.

    This fixture creates a small, throwaway database with just the tables
    needed for the insertion functions. The module-level database path is
    patched so that all inserts go to this temporary file rather than a
    real database.

    Returns
    -------
    pathlib.Path
        The path to the temporary SQLite database.
    """
    db_path = tmp_path / "test.db"

    monkeypatch.setattr(
        "clinvar_query.modules.insert_annotated_results.database_file",
        str(db_path),
    )

    # Create a minimal schema required for the tests
    con = sqlite3.connect(db_path)
    cur = con.cursor()
    cur.execute("CREATE TABLE patient_information (patient_id TEXT)")
    cur.execute(
        "CREATE TABLE variants (variant_id TEXT, patient_id TEXT, patient_variant TEXT)"
    )
    cur.execute(
        """
        CREATE TABLE clinvar (
            variant_id TEXT,
            hgvs TEXT,
            associated_conditions TEXT,
            chromosome TEXT,
            gene TEXT,
            consensus_classification TEXT,
            star_rating TEXT,
            allele_frequency REAL
        )
        """
    )
    con.commit()
    con.close()

    return db_path


def test_insert_patient_information(temp_db):
    """
    Check that patient information is inserted correctly.

    A single patient record should be written to the
    `patient_information` table.
    """
    expected = [("P001",)]

    insert_patient_information({"patient_id": "P001"})

    con = sqlite3.connect(temp_db)
    result = con.execute("SELECT patient_id FROM patient_information").fetchall()
    con.close()

    logger.info(f"testing insert_patient_information: {result}")
    assert expected == result


def test_insert_variants(temp_db):
    """
    Check that variant records are inserted correctly.

    This test confirms that the variant ID, patient ID and combined
    patient–variant identifier are stored as expected.
    """
    expected = [("V1", "P001", "P001_V1")]

    insert_variants(
        {
            "variant_id": "V1",
            "patient_id": "P001",
            "patient_variant": "P001_V1",
        }
    )

    con = sqlite3.connect(temp_db)
    result = con.execute(
        "SELECT variant_id, patient_id, patient_variant FROM variants"
    ).fetchall()
    con.close()

    logger.info(f"testing insert_variants: {result}")
    assert expected == result


def test_insert_clinvar(temp_db):
    """
    Check that ClinVar annotation data is inserted correctly.

    The test focuses on a small subset of fields to confirm that ClinVar
    data (such as the gene symbol and allele frequency) is persisted
    correctly.
    """
    expected = [("V1", "GENE1", 0.12)]

    insert_clinvar(
        {
            "variant_id": "V1",
            "hgvs": "NM_000000.1:c.1A>T",
            "associated_conditions": "ConditionX",
            "chromosome": "1",
            "gene": "GENE1",
            "consensus_classification": "Pathogenic",
            "star_rating": "★★",
            "allele_frequency": 0.12,
        }
    )

    con = sqlite3.connect(temp_db)
    result = con.execute(
        "SELECT variant_id, gene, allele_frequency FROM clinvar"
    ).fetchall()
    con.close()

    logger.info(f"testing insert_clinvar: {result}")
    assert expected == result
