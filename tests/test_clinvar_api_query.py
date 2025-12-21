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
    def info(self, *args): pass
    def warning(self, *args): pass
    def debug(self, *args): pass
    def error(self, *args): pass


@pytest.fixture(autouse=True)
def patch_logger():
    """Replace the real logger with a fake logger for all tests."""
    with patch.object(module, "logger", FakeLogger()):
        yield


# -------------------------------------------------------------------
# search_clinvar tests
# -------------------------------------------------------------------
def test_search_clinvar_success():
    mock_resp = MagicMock()
    mock_resp.raise_for_status.return_value = None
    mock_resp.json.return_value = {"esearchresult": {"idlist": ["111", "222"]}}

    with patch("requests.get", return_value=mock_resp):
        assert module.search_clinvar("NM_111:g.1A>T") == ["111", "222"]


def test_search_clinvar_error():
    with patch("requests.get", side_effect=Exception("boom")):
        assert module.search_clinvar("ERR") == []


# -------------------------------------------------------------------
# get_esummary tests
# -------------------------------------------------------------------
def test_get_esummary_success():
    mock_resp = MagicMock()
    mock_resp.raise_for_status.return_value = None
    mock_resp.json.return_value = {"result": {"111": {"ok": True}}}

    with patch("requests.get", return_value=mock_resp):
        assert module.get_esummary(["111"]) == {"111": {"ok": True}}


def test_get_esummary_empty_input():
    assert module.get_esummary([]) == {}


def test_get_esummary_error():
    with patch("requests.get", side_effect=Exception("fail")):
        assert module.get_esummary(["1"]) == {}


# -------------------------------------------------------------------
# process_clinvar tests
# -------------------------------------------------------------------
def test_process_clinvar_no_json_files(tmp_path):
    outdir = tmp_path / "out"
    outdir.mkdir()

    module.process_clinvar(tmp_path, outdir)


def test_process_clinvar_load_error(tmp_path):
    outdir = tmp_path / "out"
    outdir.mkdir()

    infile = tmp_path / "bad.json"
    infile.write_text("invalid json")

    def failing_open(*a, **k):
        raise Exception("read error")

    with patch("builtins.open", failing_open):
        module.process_clinvar(tmp_path, outdir)


def test_process_clinvar_missing_variant(tmp_path):
    outdir = tmp_path / "out"
    outdir.mkdir()

    infile = tmp_path / "file.json"
    infile.write_text(json.dumps([{"foo": "bar"}]))

    module.process_clinvar(tmp_path, outdir)

    out = (outdir / "file.json").read_text()
    assert out == "[]"


def test_process_clinvar_missing_g_hgvs_keyerror(tmp_path):
    outdir = tmp_path / "out"
    outdir.mkdir()

    entry = [{"variant": "V1", "result": {}}]
    infile = tmp_path / "file.json"
    infile.write_text(json.dumps(entry))

    module.process_clinvar(tmp_path, outdir)

    out = json.loads((outdir / "file.json").read_text())
    assert out == []


def test_process_clinvar_missing_g_hgvs_nested(tmp_path):
    outdir = tmp_path / "out"
    outdir.mkdir()

    entry = [{"variant": "V1", "result": {"V1": {"V1": {}}}}]
    infile = tmp_path / "file.json"
    infile.write_text(json.dumps(entry))

    module.process_clinvar(tmp_path, outdir)

    out = json.loads((outdir / "file.json").read_text())
    assert out == []


def test_process_clinvar_success(tmp_path):
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
        return search_resp if "esearch" in url else summary_resp

    with patch("requests.get", get_mock):
        module.process_clinvar(tmp_path, outdir)

    out = json.loads((outdir / "file.json").read_text())
    assert out[0]["clinvar_ids"] == ["100"]
    assert out[0]["esummary"] == {"100": {"foo": "bar"}}


def test_process_clinvar_write_error(tmp_path):
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





