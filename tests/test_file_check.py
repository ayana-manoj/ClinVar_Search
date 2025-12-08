from clinvar_query.modules.check_file_status import app_file_check
from clinvar_query.logger import logger
from pathlib import Path
import os
import pytest


process_file = "tests/test_files/Patient1.vcf"
misalign_file = "tests/test_files/Patient5.csv"
overwrite = False

def test_file_check_processed_file():
    processed_file, misaligned_file, status = app_file_check(
                                                process_file,
                                                overwrite=overwrite)
    assert status == "created"

def test_file_check_misaligned_file():
    processed_file, misaligned_file, status = app_file_check(
                                                misalign_file,
                                                overwrite=overwrite)
    assert status == "created"


# def app_file_check_process_file_overwrite():
#     processed_file, misaligned_file, status = app_file_check(
#                                                 process_file,
#                                                 overwrite=overwrite)
#     assert status == "created"

