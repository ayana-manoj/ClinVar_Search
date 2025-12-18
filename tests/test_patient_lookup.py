from clinvar_query.modules.patient_lookup import lookup
import pytest

database_file = "tests/test_db/test.db"

def test_lookup_latest_results():
    database = database_file
    latest_results = []
    files = []
    misaligned = []

    latest_results, files, misaligned = lookup(latest_results,
                                               files,
                                               misaligned,
                                               database)
    expected_results = []

    assert latest_results == expected_results