from .test_db.lookup_results import lookup_list
from clinvar_query.modules.patient_lookup import lookup
import pytest

"""This tests the patient lookup module
since this executes a sql query, some dummy data in the test folder was created
This allows for testing new implementations of the database if changes are needed
For database lookup (latest results), this looks for:
Normal use case
No database

For file lookup (processed and misaligned files), this looks for:
Normal files 
Error files 
Empty files

"""

database_file = "tests/test_db/test.db"
processed_folder = "tests/test_files/test_processed"
error_folder = "tests/test_files/test_error"
empty_folder = "tests/test_files/empty_folder"


def test_lookup_latest_results():
    database = database_file
    latest_results = []
    files = []
    misaligned = []

    latest_results, _, _ = lookup(
        latest_results,
        files,
        misaligned,
        database,
        process_folder=processed_folder,
        err_folder=error_folder
    )

    # Extract variants from latest_results (column 1)
    result_variants = sorted({row[1] for row in latest_results})

    # Extract expected variants from lookup_list (column 0)
    expected_variants = sorted({row[0] for row in lookup_list})

    assert result_variants == expected_variants


def test_lookup_no_database():
    with pytest.raises(UnboundLocalError):
        database = database  # intentionally undefined
        latest_results = []
        files = []
        misaligned = []

        lookup(
            latest_results,
            files,
            misaligned,
            database,
            process_folder=processed_folder,
            err_folder=error_folder
        )


def test_lookup_files():
    database = database_file
    latest_results = []
    files = []
    misaligned = []

    _, files, _ = lookup(
        latest_results,
        files,
        misaligned,
        database,
        process_folder=processed_folder,
        err_folder=error_folder
    )

    expected_files = [
        "test_data_processed.txt",
        "test5_processed.txt",
        "test1_processed.txt",
    ]

    assert sorted(files) == sorted(expected_files)


def test_empty_files():
    database = database_file
    latest_results = []
    files = []
    misaligned = []

    _, files, _ = lookup(
        latest_results,
        files,
        misaligned,
        database,
        process_folder=empty_folder,
        err_folder=error_folder
    )

    assert files == []


def test_error_files():
    database = database_file
    latest_results = []
    files = []
    misaligned = []

    _, _, misaligned = lookup(
        latest_results,
        files,
        misaligned,
        database,
        process_folder=processed_folder,
        err_folder=error_folder
    )

    expected_error_files = [
        "misaligned_test5_processed.txt",
        "misaligned_output.txt",
    ]

    assert sorted(misaligned) == sorted(expected_error_files)


def test_empty_error_files():
    database = database_file
    latest_results = []
    files = []
    misaligned = []

    _, _, misaligned = lookup(
        latest_results,
        files,
        misaligned,
        database,
        process_folder=processed_folder,
        err_folder=empty_folder
    )

    assert misaligned == []
