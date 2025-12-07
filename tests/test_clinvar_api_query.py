import json
import pytest
import os
import importlib
from unittest.mock import patch, MagicMock
from pathlib import Path

# Import the module under test
import clinvar_query.modules.clivar_api_query as module


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
    """Automatically replace the logger for all tests."""
    with patch.object(module, "logger", FakeLogger()):
        yield


# -------------------------------------------------------------------
# search_clinvar
# -------------------------------------------------------------------

def test_search_clinvar_success():
    mock_resp = MagicMock()
    mock_resp.raise_for_status.return_value = None
    mock_resp.json.return_value = {
        "esearchresult": {"idlist": ["111", "222"]}
    }

    with patch("requests.get", return_value=mock_resp):
        assert module.search_clinvar("NM_111:g.1A>T") == ["111", "222"]


def test_search_clinvar_error():
    with patch("requests.get", side_effect=Exception("boom")):
        assert module.search_clinvar("ERR") == []


# -------------------------------------------------------------------
# get_esummary
# -------------------------------------------------------------------

def test_get_esummary_success():
    mock_resp = MagicMock()
    mock_resp.raise_for_status.return_value = None
    mock_resp.json.return_value = {"result": {"111": {"ok": True}}}

    with patch("requests.get", return_value=mock_resp):
        assert module.get_esummary(["111"]) == {"111": {"ok": True}}


def test_get_esummary_empty_list():
    assert module.get_esummary([]) == {}


def test_get_esummary_error():
    with patch("requests.get", side_effect=Exception("fail")):
        assert module.get_esummary(["1"]) == {}


# -------------------------------------------------------------------
# Helper: reload with patched directories
# -------------------------------------------------------------------

def reload_with_dirs(monkeypatch, input_dir, output_dir):
    """Patch global names BEFORE reload so top-level code uses them."""
    monkeypatch.setitem(module.__dict__, "input_dir", str(input_dir))
    monkeypatch.setitem(module.__dict__, "output_dir", str(output_dir))
    return importlib.reload(module)


# -------------------------------------------------------------------
# Top-level script execution tests
# -------------------------------------------------------------------

def test_no_json_files(tmp_path, monkeypatch):
    outdir = tmp_path / "out"

    # Path.glob will return empty list
    monkeypatch.setattr(Path, "glob", lambda *a, **k: [])

    reload_with_dirs(monkeypatch, tmp_path, outdir)
    # Should simply log a warning; nothing else to check.


def test_file_read_failure(tmp_path, monkeypatch):
    infile = tmp_path / "bad.json"
    infile.write_text("doesnt matter")

    outdir = tmp_path / "out"

    def failing_open(*a, **k):
        raise Exception("read error")

    monkeypatch.setattr("builtins.open", failing_open)

    reload_with_dirs(monkeypatch, tmp_path, outdir)
    # Should not crash.


def test_missing_variant_field(tmp_path, monkeypatch):
    outdir = tmp_path / "out"
    outdir.mkdir()

    infile = tmp_path / "file.json"
    infile.write_text(json.dumps([{"foo": "bar"}]))

    reload_with_dirs(monkeypatch, tmp_path, outdir)

    out = json.loads((outdir / "file.json").read_text())
    assert out == []


def test_missing_g_hgvs(tmp_path, monkeypatch):
    outdir = tmp_path / "out"
    outdir.mkdir()

    entry = [{
        "variant": "VAR1",
        "result": {"VAR1": {"VAR1": {}}}  # no g_hgvs
    }]
    infile = tmp_path / "file.json"
    infile.write_text(json.dumps(entry))

    reload_with_dirs(monkeypatch, tmp_path, outdir)

    out = json.loads((outdir / "file.json").read_text())
    assert out == []


def test_successful_processing(tmp_path, monkeypatch):
    outdir = tmp_path / "out"
    outdir.mkdir()

    entry = [{
        "variant": "VAR1",
        "result": {"VAR1": {"VAR1": {"g_hgvs": "NC_1:g.123A>T"}}}
    }]
    infile = tmp_path / "file.json"
    infile.write_text(json.dumps(entry))

    # Mock ClinVar
    search_mock = MagicMock()
    search_mock.raise_for_status.return_value = None
    search_mock.json.return_value = {"esearchresult": {"idlist": ["123"]}}

    summary_mock = MagicMock()
    summary_mock.raise_for_status.return_value = None
    summary_mock.json.return_value = {"result": {"123": {"foo": "bar"}}}

    def get_mock(url, params):
        return search_mock if "esearch" in url else summary_mock

    with patch("requests.get", get_mock):
        reload_with_dirs(monkeypatch, tmp_path, outdir)

    out = json.loads((outdir / "file.json").read_text())
    assert out[0]["clinvar_ids"] == ["123"]
    assert out[0]["esummary"] == {"123": {"foo": "bar"}}


def test_json_write_failure(tmp_path, monkeypatch):
    outdir = tmp_path / "out"
    outdir.mkdir()

    entry = [{
        "variant": "VAR1",
        "result": {"VAR1": {"VAR1": {"g_hgvs": "NC:1"}}}
    }]
    infile = tmp_path / "file.json"
    infile.write_text(json.dumps(entry))

    mock_resp = MagicMock()
    mock_resp.raise_for_status.return_value = None
    mock_resp.json.return_value = {"esearchresult": {"idlist": []}}

    with patch("requests.get", return_value=mock_resp), \
         patch("json.dump", side_effect=Exception("write error")):
        reload_with_dirs(monkeypatch, tmp_path, outdir)

    # No crash expected



