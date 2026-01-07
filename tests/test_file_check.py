from clinvar_query.modules.check_file_status import app_file_check
from clinvar_query.utils.logger import logger
from pathlib import Path
import os
import pytest

"""Test for checking the outcome of file processing
This is a set of tests which check the outputs of the app_file_check module
This tests:
Processed files with no errors
Misaligned files
The status of files, whether created, skipped or overwritten
"""

process_file = "tests/test_files/test1.csv"
misalign_file = "tests/test_files/test5.csv"
process_folder = "tests/test_files/test_processed"
err_folder = "tests/test_files/test_error"
overwrite = False

def test_file_check_processed_file(tmp_path):
    p_folder = tmp_path/"p_folder"
    e_folder = tmp_path/"e_folder"
    o_folder = tmp_path/"o_folder"

    p_folder.mkdir(parents=True, exist_ok=True)
    e_folder.mkdir(parents=True, exist_ok=True)
    o_folder.mkdir(parents=True, exist_ok=True)
    processed_file, misaligned_file, status = app_file_check(
                                                process_file,
                                                processed_folder=p_folder,
                                                error_folder=e_folder,
                                                overwrite=overwrite)
    assert status == "created"

def test_file_check_misaligned_file(tmp_path):
    p_folder = tmp_path/"p_folder"
    e_folder = tmp_path/"e_folder"
    o_folder = tmp_path/"o_folder"

    p_folder.mkdir(parents=True, exist_ok=True)
    e_folder.mkdir(parents=True, exist_ok=True)
    o_folder.mkdir(parents=True, exist_ok=True)
    processed_file, misaligned_file, status = app_file_check(
                                                misalign_file,
                                                processed_folder=p_folder,
                                                error_folder=e_folder,                                                
                                                overwrite=overwrite)
    assert status == "created"

def test_file_check_skipped_process_file():

    processed_file, misaligned_file, status = app_file_check(
                                                process_file,
                                                processed_folder=process_folder,
                                                error_folder=err_folder,                                                
                                                overwrite=overwrite)
    assert status == "skipped"


def test_file_skipped_misaligned_file():

    processed_file, misaligned_file, status = app_file_check(
                                                misalign_file,
                                                processed_folder=process_folder,
                                                error_folder=err_folder,                                                
                                                overwrite=overwrite)
    assert status == "skipped"
