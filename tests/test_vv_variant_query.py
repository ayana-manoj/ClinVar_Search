import json
import pytest
import os
from unittest.mock import patch, MagicMock, mock_open
from pathlib import Path

from clinvar_query.modules import vv_variant_query as module


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
    """Automatically replace the logger in every test."""
    with patch.object(module, "logger", FakeLogger()):
        yield


# -------------------------------------------------------------------
# Test: No input files found
# -------------------------------------------------------------------
def test_no_input_files():
    """Ensure early return occurs when no input files exist."""
    with patch("glob.glob", return_value=[]), \
         patch("os.makedirs", side_effect=os.makedirs) as mk:

        module.vv_variant_query()

        mk.assert_called_once_with(module.output_folder, exist_ok=True)



# -------------------------------------------------------------------
# Test: File cannot be read (I/O error)
# -------------------------------------------------------------------
def test_file_read_failure(tmp_path):
    """Simulate a read error on an input file."""
    fake_file = tmp_path / "file.txt"

    with patch("glob.glob", return_value=[str(fake_file)]), \
         patch("builtins.open", side_effect=Exception("read error")):

        module.vv_variant_query()
        # No crash = pass


# -------------------------------------------------------------------
# Test: Successful run including multiple variants + JSON write
# -------------------------------------------------------------------
def test_successful_processing(tmp_path):
    """Test full successful workflow: read file, call API, write JSON."""
    input_file = tmp_path / "variants.txt"
    input_file.write_text("NM_0001.1:c.123A>G\nNM_0002.1:c.456C>T\n")

    with patch.object(module, "input_file_pattern", str(input_file)), \
         patch.object(module, "output_folder", str(tmp_path / "out")), \
         patch("glob.glob", return_value=[str(input_file)]):

        # Mock successful API response
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
# Test: API returns error (404 etc.)
# -------------------------------------------------------------------
def test_api_failure(tmp_path):
    """API returns non-200 status code; error should be recorded."""
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
            assert "error" in data[0]
            assert "(404)" in data[0]["error"]


# -------------------------------------------------------------------
# Test: Exception during API call
# -------------------------------------------------------------------
def test_api_exception(tmp_path):
    """Simulate a thrown exception during requests.get() call."""
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
    """Simulate a failure when writing the JSON output file."""
    input_file = tmp_path / "variants.txt"
    input_file.write_text("NM_0007.1:c.100A>C")

    with patch.object(module, "input_file_pattern", str(input_file)), \
         patch.object(module, "output_folder", str(tmp_path / "out")), \
         patch("glob.glob", return_value=[str(input_file)]), \
         patch("requests.get", return_value=MagicMock(status_code=200,
                                                      json=lambda: {"ok": True})), \
         patch("json.dump", side_effect=Exception("write error")):

        module.vv_variant_query()
        # Should not crash; error gets logged
