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
                - process_clinvar: various scenarios including
                    * missing fields
                    * invalid JSON input
                    * file writing errors
                    * successful end-to-end processing

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
    """
       Minimal logger stub used to suppress real logging output during tests.

       This class implements the logging methods used by the target module
       but performs no actions, ensuring clean test output.
       """

    def info(self, *args): pass #Silence info-level log messages
    def warning(self, *args): pass #Silence warning-level log messages
    def debug(self, *args): pass #Silence debug-level log messages
    def error(self, *args): pass #Silence error-level log messages


@pytest.fixture(autouse=True)
def patch_logger():
    #Replace the real logger with a fake logger for all tests.
    with patch.object(module, "logger", FakeLogger()):
        yield


# -------------------------------------------------------------------
# search_clinvar tests
# -------------------------------------------------------------------
def test_search_clinvar_success():
    """
       Verify that ``search_clinvar`` returns a list of ClinVar IDs
       when the API responds successfully.
       """
    mock_resp = MagicMock()
    mock_resp.raise_for_status.return_value = None
    mock_resp.json.return_value = {"esearchresult": {"idlist": ["111", "222"]}}

    with patch("requests.get", return_value=mock_resp):
        assert module.search_clinvar("NM_111:g.1A>T") == ["111", "222"]


def test_search_clinvar_error():
    """
       Verify that ``search_clinvar`` returns an empty list when
       an exception occurs during the API request.
       """
    with patch("requests.get", side_effect=Exception("boom")):
        assert module.search_clinvar("ERR") == []


# -------------------------------------------------------------------
# get_esummary tests
# -------------------------------------------------------------------
def test_get_esummary_success():
    """
       Verify that ``get_esummary`` returns a summary dictionary
       when valid ClinVar IDs are provided.
       """
    mock_resp = MagicMock()
    mock_resp.raise_for_status.return_value = None
    mock_resp.json.return_value = {"result": {"111": {"ok": True}}}

    with patch("requests.get", return_value=mock_resp):
        assert module.get_esummary(["111"]) == {"111": {"ok": True}}


def test_get_esummary_empty_input():
    """
       Verify that ``get_esummary`` returns an empty dictionary
       when provided with an empty ID list.
       """
    assert module.get_esummary([]) == {}


def test_get_esummary_error():
    """
        Verify that ``get_esummary`` returns an empty dictionary
        when an exception occurs during the API request.
        """
    with patch("requests.get", side_effect=Exception("fail")):
        assert module.get_esummary(["1"]) == {}


# -------------------------------------------------------------------
# process_clinvar tests
# -------------------------------------------------------------------
def test_process_clinvar_no_json_files(tmp_path):
    """
       Verify that ``process_clinvar`` exits gracefully when no
       input JSON files are present.
       """
    outdir = tmp_path / "out"
    outdir.mkdir()

    module.process_clinvar(tmp_path, outdir)


def test_process_clinvar_load_error(tmp_path):
    """
       Verify that ``process_clinvar`` handles file read errors
       without raising uncaught exceptions.
       """
    outdir = tmp_path / "out"
    outdir.mkdir()

    infile = tmp_path / "bad.json"
    infile.write_text("invalid json")

    def failing_open(*a, **k): #Simulate a file read failure
        raise Exception("read error")

    with patch("builtins.open", failing_open):
        module.process_clinvar(tmp_path, outdir)


def test_process_clinvar_missing_variant(tmp_path):
    """
        Verify that entries missing the ``variant`` key are skipped
        and result in an empty output file.
        """
    outdir = tmp_path / "out"
    outdir.mkdir()

    infile = tmp_path / "file.json"
    infile.write_text(json.dumps([{"foo": "bar"}]))

    module.process_clinvar(tmp_path, outdir)

    out = (outdir / "file.json").read_text()
    assert out == "[]"


def test_process_clinvar_missing_g_hgvs_keyerror(tmp_path):
    """
       Verify that entries missing the ``g_hgvs`` field raise no
       errors and are excluded from output.
       """
    outdir = tmp_path / "out"
    outdir.mkdir()

    entry = [{"variant": "V1", "result": {}}]
    infile = tmp_path / "file.json"
    infile.write_text(json.dumps(entry))

    module.process_clinvar(tmp_path, outdir)

    out = json.loads((outdir / "file.json").read_text())
    assert out == []


def test_process_clinvar_missing_g_hgvs_nested(tmp_path):
    """
        Verify that deeply nested but incomplete result structures
        are handled safely.
        """
    outdir = tmp_path / "out"
    outdir.mkdir()

    entry = [{"variant": "V1", "result": {"V1": {"V1": {}}}}]
    infile = tmp_path / "file.json"
    infile.write_text(json.dumps(entry))

    module.process_clinvar(tmp_path, outdir)

    out = json.loads((outdir / "file.json").read_text())
    assert out == []


def test_process_clinvar_success(tmp_path):
    """
        Verify successful end-to-end processing of a valid variant,
        including ClinVar search and summary retrieval.
        """
    outdir = tmp_path / "out"
    outdir.mkdir()

    entry = [
        {
            "variant": "V1",
            "result": {
                "V1": {
                    "V1": {"g_hgvs": "NC_1:g.123A>T"}
                }
            }
        }
    ]
    infile = tmp_path / "file.json"
    infile.write_text(json.dumps(entry))

    search_resp = MagicMock()
    search_resp.raise_for_status.return_value = None
    search_resp.json.return_value = {"esearchresult": {"idlist": ["100"]}}

    summary_resp = MagicMock()
    summary_resp.raise_for_status.return_value = None
    summary_resp.json.return_value = {"result": {"100": {"foo": "bar"}}}

    def get_mock(url, params):
        """Route mocked requests based on URL content."""
        return search_resp if "esearch" in url else summary_resp

    with patch("requests.get", get_mock):
        module.process_clinvar(tmp_path, outdir)

    out = json.loads((outdir / "file.json").read_text())
    assert out[0]["clinvar_ids"] == ["100"]
    assert out[0]["esummary"] == {"100": {"foo": "bar"}}


def test_process_clinvar_write_error(tmp_path):
    """
        Verify that write failures during JSON output do not crash
        the processing pipeline.
        """
    outdir = tmp_path / "out"
    outdir.mkdir()

    entry = [{"variant": "V1", "result": {"V1": {"V1": {"g_hgvs": "NC:1"}}}}]
    infile = tmp_path / "file.json"
    infile.write_text(json.dumps(entry))

    mock_resp = MagicMock()
    mock_resp.raise_for_status.return_value = None
    mock_resp.json.return_value = {"esearchresult": {"idlist": []}}

    with patch("requests.get", return_value=mock_resp), \
         patch("json.dump", side_effect=Exception("write error")):
        module.process_clinvar(tmp_path, outdir)





