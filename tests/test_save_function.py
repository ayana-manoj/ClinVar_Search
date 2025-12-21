from clinvar_query.modules.save_function import save_output_to_file
from clinvar_query.utils.logger import logger
from clinvar_query.modules.parser import parser
from pathlib import Path
import os
import pytest
"""
This tests the save function
it was originally in the app.py
now has been separated and will be tested

"""
processed_folder = "tests/test_files/test_processed"
data = "tests/test_files/test1.csv"
saved_file = None
misaligned_file = None
title = "test_data"
overwrite = False


def test_save_function(tmp_path):
    processed_data, misaligned_data = parser(data)
    output_path, status = save_output_to_file(processed_data,
                                              title,
                                              folder=tmp_path/"test_processed",
                                              overwrite=overwrite)
    logger.info(f"testing for save functionality")
    assert output_path == str(tmp_path/"test_processed/test_data_processed.txt")
    assert status == "created"
    assert os.path.isfile(output_path)


def test_save_function_skip():
    processed_data, misaligned_data = parser(data)
    saved_file, status = save_output_to_file(processed_data,
                                            title,
                                            folder="tests/test_files/test_processed",
                                            overwrite=overwrite)
    logger.info(f"testing for skipping if a file exists and overwrite is false")
    assert saved_file == None
    assert status == "skipped"


def test_save_function_Error(tmp_path):
    processed_data = None
    saved_file, status = save_output_to_file(processed_data,
                                            title,
                                            folder=tmp_path/"test_processed",
                                            overwrite=overwrite)
    logger.info(f"testing for error, when processed data is empty")
    assert saved_file == None
    assert status == "error"


def test_save_function_overwrite():
    overwrite = True
    processed_data, misaligned_data = parser(data)
    output_path, status = save_output_to_file(processed_data,
                                              title,
                                              folder="tests/test_files/test_processed",
                                              overwrite=overwrite)
    logger.info(f"testing for skipping if a file exists and overwrite is false")
    assert output_path == "tests/test_files/test_processed/test_data_processed.txt"
    assert status == "overwritten"
