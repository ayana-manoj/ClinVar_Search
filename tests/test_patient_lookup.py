from clinvar_query.modules.patient_lookup import lookup
from tests.test_db.lookup_results import lookup_list
import pytest


database_file = "tests/test_db/test.db"
processed_folder = "tests/test_files/test_processed"
error_folder = "tests/test_files/test_error"
empty_folder = "tests/test_files/empty_folder"


def test_lookup_latest_results():
    database = database_file
    latest_results = []
    files = []
    misaligned = []

    latest_results, files, misaligned = lookup(latest_results,
                                               files,
                                               misaligned,
                                               database,
                                               process_folder=processed_folder,
                                               err_folder=error_folder)
    expected_results = lookup_list

    results = [list(row) for row in latest_results]
    assert results == expected_results


def test_lookup_no_database():
    with pytest.raises(UnboundLocalError):
        database = database
        latest_results = []
        files = []
        misaligned = []

        latest_results, files, misaligned = lookup(latest_results,
                                                   files,
                                                   misaligned,
                                                   database,
                                                   process_folder=processed_folder,
                                                   err_folder=error_folder)


def test_lookup_files():
    database = database_file
    latest_results = []
    files = []
    misaligned = []

    latest_results, files, misaligned = lookup(latest_results,
                                               files,
                                               misaligned,
                                               database,
                                               process_folder=processed_folder,
                                               err_folder=error_folder)
    expected_files = ['test_data_processed.txt', 'test5_processed.txt', 'test1_processed.txt']

    assert files == expected_files


def test_empty_files():
    database = database_file
    latest_results = []
    files = []
    misaligned = []

    latest_results, files, misaligned = lookup(latest_results,
                                               files,
                                               misaligned,
                                               database,
                                               process_folder=empty_folder,
                                               err_folder=error_folder)
    expected_files = []

    assert files == expected_files


def test_error_files():
    database = database_file
    latest_results = []
    files = []
    misaligned = []

    latest_results, files, misaligned = lookup(latest_results,
                                               files,
                                               misaligned,
                                               database,
                                               process_folder=processed_folder,
                                               err_folder=error_folder)
    expected_error_files = ['misaligned_test5_processed.txt','misaligned_output.txt',]

    assert misaligned == expected_error_files


def test_empty_error_files():
    database = database_file
    latest_results = []
    files = []
    misaligned = []

    latest_results, files, misaligned = lookup(latest_results,
                                               files,
                                               misaligned,
                                               database,
                                               process_folder=processed_folder,
                                               err_folder=empty_folder)
    expected_error_files = []

    assert misaligned == expected_error_files
