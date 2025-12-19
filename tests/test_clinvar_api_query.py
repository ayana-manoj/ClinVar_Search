"""

*********** CREATED USING HELP OF CHATGPT ***********

===============================================================================
Test Suite for clinvar_api_query.py
===============================================================================

Title:        test_clinvar_api_query.py
Module:       clinvar_query.modules.clinvar_api_query
Purpose:      Unit tests for the clinvar_api_query module.

              This test suite covers:
                - search_clinvar: success and error handling
                - get_esummary: success, empty input, and error handling
                - process_files: various scenarios including
                    * missing fields
                    * invalid JSON input
                    * file writing errors
                    * successful end-to-end processing

              All tests use pytest fixtures and unittest.mock to isolate
              filesystem and API dependencies, ensuring reproducible results.

Notes:
    - pytest is used for test discovery and execution.
    - unittest.mock is used for patching logger, requests, and file I/O.
    - A fake logger is used to suppress log output during tests.

===============================================================================
"""

import json
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path

# Import the module under test
from clinvar_query.modules import clinvar_api_query as module


# -------------------------------------------------------------------
# Fake logger to silence real log output during tests
# -------------------------------------------------------------------
class FakeLogger:
    """A logger that does nothing, used to suppress output during tests."""
    def info(self, *args): pass
    def warning(self, *args): pass
    def debug(self, *args): pass
    def error(self, *args): pass


@pytest.fixture(autouse=True)
def patch_logger():
    """
    Automatically replace the logger in clinvar_api_query with FakeLogger
    for all tests to prevent cluttering test output.
    """
    with patch.object(module, "logger", FakeLogger()):
        yield


# -------------------------------------------------------------------
# search_clinvar tests
# -------------------------------------------------------------------
def test_search_clinvar_success():
    """Test that search_clinvar returns a list of IDs on successful API call."""
    mock_resp = MagicMock()
    mock_resp.raise_for_status.return_value = None
    mock_resp.json.return_value = {"esearchresult": {"idlist": ["111", "222"]}}

    with patch("requests.get", return_value=mock_resp):
        assert module.search_clinvar("NM_111:g.1A>T") == ["111", "222"]


def test_search_clinvar_error():
    """Test that search_clinvar returns an empty list if an exception occurs."""
    with patch("requests.get", side_effect=Exception("boom")):
        assert module.search_clinvar("ERR") == []


# -------------------------------------------------------------------
# get_esummary tests
# -------------------------------------------------------------------
def test_get_esummary_success():
    """Test that get_esummary returns a dictionary of results on success."""
    mock_resp = MagicMock()
    mock_resp.raise_for_status.return_value = None
    mock_resp.json.return_value = {"result": {"111": {"ok": True}}}

    with patch("requests.get", return_value=mock_resp):
        assert module.get_esummary(["111"]) == {"111": {"ok": True}}


def test_get_esummary_empty_input():
    """Test that get_esummary returns an empty dict if input list is empty."""
    assert module.get_esummary([]) == {}


def test_get_esummary_error():
    """Test that get_esummary returns an empty dict if an exception occurs."""
    with patch("requests.get", side_effect=Exception("fail")):
        assert module.get_esummary(["1"]) == {}


# -------------------------------------------------------------------
# process_files tests
# -------------------------------------------------------------------
def test_process_files_no_json_files(tmp_path):
    """Test that process_files handles directories with no JSON files gracefully."""
    outdir = tmp_path / "out"
    outdir.mkdir()
    module.process_files(tmp_path, outdir)


def test_process_files_load_error(tmp_path):
    """Test that process_files handles JSON load errors without crashing."""
    outdir = tmp_path / "out"
    outdir.mkdir()

    infile = tmp_path / "bad.json"
    infile.write_text("invalid json")

    def failing_open(*a, **k):
        raise Exception("read error")

    with patch("builtins.open", failing_open):
        module.process_files(tmp_path, outdir)


def test_process_files_missing_variant(tmp_path):
    """
    Test that process_files handles entries missing 'variant' key.
    Output file should contain an empty list.
    """
    outdir = tmp_path / "out"
    outdir.mkdir()

    infile = tmp_path / "file.json"
    infile.write_text(json.dumps([{"foo": "bar"}]))

    module.process_files(tmp_path, outdir)

    out = (outdir / "file.json").read_text()
    assert out == "[]"


def test_process_files_missing_g_hgvs_keyerror(tmp_path):
    """
    Test that process_files handles nested KeyError when g_hgvs is missing.
    Output file should be an empty list.
    """
    outdir = tmp_path / "out"
    outdir.mkdir()

    entry = [{"variant": "V1", "result": {}}]  # triggers KeyError
    infile = tmp_path / "file.json"
    infile.write_text(json.dumps(entry))

    module.process_files(tmp_path, outdir)

    out = json.loads((outdir / "file.json").read_text())
    assert out == []


def test_process_files_missing_g_hgvs_nested(tmp_path):
    """
    Test that process_files handles nested structure where g_hgvs is missing.
    Output file should be an empty list.
    """
    outdir = tmp_path / "out"
    outdir.mkdir()

    entry = [{"variant": "V1", "result": {"V1": {"V1": {}}}}]  # g_hgvs missing
    infile = tmp_path / "file.json"
    infile.write_text(json.dumps(entry))

    module.process_files(tmp_path, outdir)

    out = json.loads((outdir / "file.json").read_text())
    assert out == []


def test_process_files_success(tmp_path):
    """
    Test that process_files successfully processes a valid JSON file,
    queries the API, and writes the correct output.
    """
    outdir = tmp_path / "out"
    outdir.mkdir()

    # Input file with valid variant
    entry = [{"variant": "V1", "result": {"V1": {"V1": {"g_hgvs": "NC_1:g.123A>T"}}}}]
    infile = tmp_path / "file.json"
    infile.write_text(json.dumps(entry))

    # Mock the API responses
    search_resp = MagicMock()
    search_resp.raise_for_status.return_value = None
    search_resp.json.return_value = {"esearchresult": {"idlist": ["100"]}}

    summary_resp = MagicMock()
    summary_resp.raise_for_status.return_value = None
    summary_resp.json.return_value = {"result": {"100": {"foo": "bar"}}}

    # Patch requests.get to return our mock responses
    def get_mock(url, params):
        return search_resp if "esearch" in url else summary_resp

    with patch("requests.get", get_mock):
        module.process_files(tmp_path, outdir)

    out = json.loads((outdir / "file.json").read_text())
    assert out[0]["clinvar_ids"] == ["100"]
    assert out[0]["esummary"] == {"100": {"foo": "bar"}}


def test_process_files_write_error(tmp_path):
    """
    Test that process_files handles exceptions during JSON file writing
    without crashing.
    """
    outdir = tmp_path / "out"
    outdir.mkdir()

    entry = [{"variant": "V1", "result": {"V1": {"V1": {"g_hgvs": "NC:1"}}}}]
    infile = tmp_path / "file.json"
    infile.write_text(json.dumps(entry))

    mock_resp = MagicMock()
    mock_resp.raise_for_status.return_value = None
    mock_resp.json.return_value = {"esearchresult": {"idlist": []}}

    # Patch requests.get and json.dump to simulate write error
    with patch("requests.get", return_value=mock_resp), \
         patch("json.dump", side_effect=Exception("write error")):
        module.process_files(tmp_path, outdir)




