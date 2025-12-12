"""

*********** CREATED USING CHATGPT ***********

===============================================================================
Test Suite for vv_variant_query.py
===============================================================================

Title:        test_vv_variant_query.py
Module:       clinvar_query.modules.vv_variant_query
Purpose:      Unit tests for the vv_variant_query module.
              This test suite covers:
                - Handling of no input files
                - File read/write errors
                - API call success and failure scenarios
                - JSON output generation
              All tests mock external dependencies (filesystem and API calls)
              to ensure reproducible and isolated testing.

Notes:
    - Uses pytest framework for test discovery and execution.
    - Uses unittest.mock for patching file I/O, requests, and logger.
    - Includes a fake logger to suppress output during testing.

===============================================================================
"""

import json
import pytest
import os
from unittest.mock import patch, MagicMock
from pathlib import Path

# Import the module under test
from clinvar_query.modules import vv_variant_query as module


# -------------------------------------------------------------------
# Fake logger to silence actual log output during tests
# -------------------------------------------------------------------
class FakeLogger:
    """A simple logger replacement that ignores all log messages."""
    def info(self, *args): pass
    def warning(self, *args): pass
    def debug(self, *args): pass
    def error(self, *args): pass


@pytest.fixture(autouse=True)
def patch_logger():
    """
    Patch the module's logger automatically for every test.

    This prevents cluttering test output with log messages.
    """
    with patch.object(module, "logger", FakeLogger()):
        yield


# -------------------------------------------------------------------
# Test: No input files
# -------------------------------------------------------------------
def test_no_input_files():
    """
    Ensure early return occurs when no input files are found.

    The function should create the output directory but perform no processing.
    """
    with patch("glob.glob", return_value=[]), \
         patch("os.makedirs", side_effect=os.makedirs) as mk:

        module.vv_variant_query()

        # The output directory should be created
        mk.assert_called_once_with(module.output_folder, exist_ok=True)


# -------------------------------------------------------------------
# Test: Input file read failure
# -------------------------------------------------------------------
def test_file_read_failure(tmp_path):
    """
    Simulate a file I/O error when attempting to read an input file.

    The function should handle the exception and not crash.
    """
    fake_file = tmp_path / "file.txt"

    with patch("glob.glob", return_value=[str(fake_file)]), \
         patch("builtins.open", side_effect=Exception("read error")):

        module.vv_variant_query()
        # Test passes if no exception is raised


# -------------------------------------------------------------------
# Test: Successful processing of multiple variants
# -------------------------------------------------------------------
def test_successful_processing(tmp_path):
    """
    Test full successful workflow:
    - Read input file
    - Query API
    - Write results to JSON
    """
    input_file = tmp_path / "variants.txt"
    input_file.write_text("NM_0001.1:c.123A>G\nNM_0002.1:c.456C>T\n")

    with patch.object(module, "input_file_pattern", str(input_file)), \
         patch.object(module, "output_folder", str(tmp_path / "out")), \
         patch("glob.glob", return_value=[str(input_file)]):

        # Mock a successful API response
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"ok": True}

        with patch("requests.get", return_value=mock_resp):
            module.vv_variant_query()

            output_file = tmp_path / "out" / "variants.json"
            assert output_file.exists()

            data = json.loads(output_file.read_text())
            assert len(data) == 2
            assert data[0]["variant"] == "NM_0001.1:c.123A>G"
            assert data[0]["result"] == {"ok": True}


# -------------------------------------------------------------------
# Test: API returns error status code
# -------------------------------------------------------------------
def test_api_failure(tmp_path):
    """
    Simulate an API response with a non-200 status code (e.g., 404).

    The function should record an error in the output JSON.
    """
    input_file = tmp_path / "variants.txt"
    input_file.write_text("NM_0003.1:c.789G>A")

    with patch.object(module, "input_file_pattern", str(input_file)), \
         patch.object(module, "output_folder", str(tmp_path / "out")), \
         patch("glob.glob", return_value=[str(input_file)]):

        mock_resp = MagicMock()
        mock_resp.status_code = 404

        with patch("requests.get", return_value=mock_resp):
            module.vv_variant_query()

            output_file = tmp_path / "out" / "variants.json"
            assert output_file.exists()

            data = json.loads(output_file.read_text())
            # The error field should indicate the status code
            assert "error" in data[0]
            assert "(404)" in data[0]["error"]


# -------------------------------------------------------------------
# Test: Exception during API call
# -------------------------------------------------------------------
def test_api_exception(tmp_path):
    """
    Simulate a raised exception during the requests.get() API call.

    The exception should be caught, and the error logged in the JSON output.
    """
    input_file = tmp_path / "variants.txt"
    input_file.write_text("NM_0005.1:c.999A>T")

    with patch.object(module, "input_file_pattern", str(input_file)), \
         patch.object(module, "output_folder", str(tmp_path / "out")), \
         patch("glob.glob", return_value=[str(input_file)]):

        with patch("requests.get", side_effect=Exception("network fail")):
            module.vv_variant_query()

            output_file = tmp_path / "out" / "variants.json"
            assert output_file.exists()

            data = json.loads(output_file.read_text())
            assert "Exception during request" in data[0]["error"]


# -------------------------------------------------------------------
# Test: JSON write failure
# -------------------------------------------------------------------
def test_json_write_failure(tmp_path):
    """
    Simulate a failure when writing the JSON output file.

    The function should handle the exception and not crash.
    """
    input_file = tmp_path / "variants.txt"
    input_file.write_text("NM_0007.1:c.100A>C")

    with patch.object(module, "input_file_pattern", str(input_file)), \
         patch.object(module, "output_folder", str(tmp_path / "out")), \
         patch("glob.glob", return_value=[str(input_file)]), \
         patch("requests.get", return_value=MagicMock(
             status_code=200, json=lambda: {"ok": True})), \
         patch("json.dump", side_effect=Exception("write error")):

        module.vv_variant_query()
        # Test passes if exception is caught and logged

