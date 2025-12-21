import json
from pathlib import Path
import builtins
import pytest

import clinvar_query.modules.json_to_db as json_to_db


# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------

def make_valid_variant(
    variant="NM_000000.1:c.1A>T",
    hgvs="g.123A>T",
    uid="12345",
    review_status="criteria provided, single submitter",
    af="0.001",
):
    return {
        "variant": variant,
        "g_hgvs": hgvs,
        "esummary": {
            "uids": [uid],
            uid: {
                "genes": [{"symbol": "BRCA1"}],
                "variation_set": [
                    {
                        "variation_loc": [{"status": "current", "chr": "17"}],
                        "allele_freq_set": [{"source": "gnomAD", "value": af}],
                    }
                ],
                "germline_classification": {
                    "description": "Pathogenic",
                    "review_status": review_status,
                    "trait_set": [{"trait_name": "Breast cancer"}],
                },
            },
        },
    }


# ---------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------

@pytest.fixture
def mock_paths(monkeypatch, tmp_path):
    monkeypatch.setattr(json_to_db, "clinvar_folder", tmp_path)
    monkeypatch.setattr(json_to_db, "database_file", tmp_path / "db.sqlite")
    return tmp_path


@pytest.fixture
def mock_inserts(monkeypatch):
    calls = {"patient": [], "variant": [], "clinvar": []}

    def insert_patient_information(data):
        calls["patient"].append(data)

    def insert_variants(data):
        calls["variant"].append(data)

    def insert_clinvar(data):
        calls["clinvar"].append(data)

    monkeypatch.setattr(json_to_db, "insert_patient_information", insert_patient_information)
    monkeypatch.setattr(json_to_db, "insert_variants", insert_variants)
    monkeypatch.setattr(json_to_db, "insert_clinvar", insert_clinvar)

    return calls


@pytest.fixture
def mock_logger(monkeypatch):
    logs = []

    class DummyLogger:
        def info(self, msg, *args, **kwargs):
            logs.append(("info", msg % args if args else msg))

        def warning(self, msg, *args, **kwargs):
            logs.append(("warning", msg % args if args else msg))

        def error(self, msg, *args, **kwargs):
            logs.append(("error", msg % args if args else msg))

        def exception(self, msg, *args, **kwargs):
            logs.append(("exception", msg % args if args else msg))

    dummy_logger = DummyLogger()
    monkeypatch.setattr(json_to_db, "logger", dummy_logger)
    return logs


# ---------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------

def test_no_json_files_logs_warning(mock_paths, mock_logger):
    json_to_db.json_to_dir()
    assert any("No JSON files found" in msg for level, msg in mock_logger)


def test_json_load_failure_logs_exception(mock_paths, monkeypatch, mock_logger):
    bad_file = mock_paths / "bad.json"
    bad_file.write_text("not json")

    def bad_open(*args, **kwargs):
        raise OSError("boom")

    monkeypatch.setattr(builtins, "open", bad_open)
    json_to_db.json_to_dir()
    assert any("Failed to load JSON file" in msg for level, msg in mock_logger)


def test_skips_malformed_entry(mock_paths, mock_logger):
    file = mock_paths / "p1_test.json"
    file.write_text(json.dumps([{"variant": None}]))
    json_to_db.json_to_dir()
    assert any("Skipping malformed entry" in msg for level, msg in mock_logger)


def test_missing_uid_skips_variant(mock_paths, mock_logger):
    file = mock_paths / "p1_test.json"
    file.write_text(json.dumps([{"variant": "v1", "g_hgvs": "g.1A>T", "esummary": {}}]))
    json_to_db.json_to_dir()
    assert any("No ClinVar UID found" in msg for level, msg in mock_logger)


def test_uid_not_found_in_summary(mock_paths, mock_logger):
    file = mock_paths / "p1_test.json"
    file.write_text(json.dumps([{"variant": "v1", "g_hgvs": "g.1A>T", "esummary": {"uids": ["1"]}}]))
    json_to_db.json_to_dir()
    assert any("ClinVar UID 1 not found" in msg for level, msg in mock_logger)


def test_valid_variant_successful_insert(mock_paths, mock_inserts, mock_logger):
    file = mock_paths / "p123_wes.json"
    file.write_text(json.dumps([make_valid_variant()]))
    json_to_db.json_to_dir()

    assert len(mock_inserts["patient"]) == 1
    assert len(mock_inserts["variant"]) == 1
    assert len(mock_inserts["clinvar"]) == 1

    clinvar = mock_inserts["clinvar"][0]
    assert clinvar["gene"] == "BRCA1"
    assert clinvar["chromosome"] == "17"
    assert clinvar["allele_frequency"] == "0.001"  # Updated to string
    assert "⭐" in clinvar["star_rating"]

    assert any("Inserted variant" in msg for level, msg in mock_logger)


def test_invalid_allele_frequency_logs_warning(mock_paths, mock_inserts, mock_logger):
    file = mock_paths / "p1_test.json"
    file.write_text(json.dumps([make_valid_variant(af="not_a_number")]))
    json_to_db.json_to_dir()

    assert any("Invalid allele frequency" in msg for level, msg in mock_logger)
    assert mock_inserts["clinvar"][0]["allele_frequency"] == "None found"  # Updated to string


def test_database_insertion_failure_is_caught(mock_paths, monkeypatch, mock_logger):
    file = mock_paths / "p1_test.json"
    file.write_text(json.dumps([make_valid_variant()]))

    def fail(*args, **kwargs):
        raise RuntimeError("db down")

    monkeypatch.setattr(json_to_db, "insert_patient_information", fail)
    json_to_db.json_to_dir()

    assert any("Database insertion failed" in msg for level, msg in mock_logger)


def test_missing_review_status_defaults_to_zero_stars(mock_paths, mock_inserts):
    variant = make_valid_variant(review_status=None)
    file = mock_paths / "p1_test.json"
    file.write_text(json.dumps([variant]))
    json_to_db.json_to_dir()

    star_rating = mock_inserts["clinvar"][0]["star_rating"]
    assert star_rating.startswith("Unknown")



