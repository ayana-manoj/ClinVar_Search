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
    """
    Create a minimal, valid ClinVar-like JSON structure.

    This helper is used throughout the test suite to generate a
    well-formed variant entry that mimics the structure returned
    by ClinVar's API. Individual fields can be overridden to test
    error handling and edge cases.

    Parameters
    ----------
    variant : str
        HGVS coding variant string.
    hgvs : str
        Genomic HGVS notation.
    uid : str
        ClinVar UID for the variant.
    review_status : str or None
        ClinVar review status used to derive star ratings.
    af : str
        Allele frequency value (string to simulate raw JSON input).

    Returns
    -------
    dict
        A dictionary representing a single ClinVar JSON entry.
    """
    return {
        # High-level variant identifier
        "variant": variant,

        # Genomic HGVS string
        "g_hgvs": hgvs,

        # ClinVar summary payload
        "esummary": {
            # List of UIDs included in the summary
            "uids": [uid],

            # UID-specific data block
            uid: {
                # Gene information
                "genes": [{"symbol": "BRCA1"}],

                # Variant location and population frequency data
                "variation_set": [
                    {
                        # Chromosome location (only current assembly used)
                        "variation_loc": [
                            {"status": "current", "chr": "17"}
                        ],

                        # Allele frequency data (e.g. gnomAD)
                        "allele_freq_set": [
                            {"source": "gnomAD", "value": af}
                        ],
                    }
                ],

                # Clinical classification metadata
                "germline_classification": {
                    "description": "Pathogenic",
                    "review_status": review_status,
                    "trait_set": [
                        {"trait_name": "Breast cancer"}
                    ],
                },
            },
        },
    }


# ---------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------

@pytest.fixture
def mock_paths(monkeypatch, tmp_path):
    """
    Mock filesystem paths used by the json_to_db module.

    This fixture redirects the ClinVar JSON directory and database
    file path to a temporary directory, ensuring tests do not touch
    real data or filesystem locations.

    Returns
    -------
    pathlib.Path
        Temporary directory path used as the mocked ClinVar folder.
    """
    monkeypatch.setattr(json_to_db, "clinvar_folder", tmp_path)
    monkeypatch.setattr(
        json_to_db,
        "database_file",
        tmp_path / "db.sqlite",
    )
    return tmp_path


@pytest.fixture
def mock_inserts(monkeypatch):
    """
    Mock database insertion functions and capture calls.

    Each mocked insert function appends its input data to a list,
    allowing assertions on what would have been written to the DB
    without performing any real database operations.

    Returns
    -------
    dict
        Dictionary containing lists of captured insert calls.
    """
    calls = {
        "patient": [],
        "variant": [],
        "clinvar": [],
    }

    def insert_patient_information(data):
        calls["patient"].append(data)

    def insert_variants(data):
        calls["variant"].append(data)

    def insert_clinvar(data):
        calls["clinvar"].append(data)

    monkeypatch.setattr(
        json_to_db,
        "insert_patient_information",
        insert_patient_information,
    )
    monkeypatch.setattr(
        json_to_db,
        "insert_variants",
        insert_variants,
    )
    monkeypatch.setattr(
        json_to_db,
        "insert_clinvar",
        insert_clinvar,
    )

    return calls


@pytest.fixture
def mock_logger(monkeypatch):
    """
    Mock logger to capture all log messages.

    This replaces the module-level logger with a dummy implementation
    that records log level and formatted message text, enabling precise
    assertions on logging behavior.

    Returns
    -------
    list
        List of tuples in the form (level, message).
    """
    logs = []

    class DummyLogger:
        """Lightweight stand-in for the standard logging.Logger."""

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
    """
    Verify a warning is logged when no JSON files are present.

    This ensures the pipeline exits gracefully without attempting
    any database operations.
    """
    json_to_db.json_to_dir()

    assert any(
        "No JSON files found" in msg
        for level, msg in mock_logger
    )


def test_json_load_failure_logs_exception(
    mock_paths,
    monkeypatch,
    mock_logger,
):
    """
    Verify JSON loading errors are caught and logged.

    Simulates a file read failure to ensure exceptions are handled
    without crashing the pipeline.
    """
    bad_file = mock_paths / "bad.json"
    bad_file.write_text("not json")

    def bad_open(*args, **kwargs):
        raise OSError("boom")

    monkeypatch.setattr(builtins, "open", bad_open)

    json_to_db.json_to_dir()

    assert any(
        "Failed to load JSON file" in msg
        for level, msg in mock_logger
    )


def test_skips_malformed_entry(mock_paths, mock_logger):
    """
    Verify malformed variant entries are skipped.

    A variant missing required fields should not trigger insertion
    attempts.
    """
    file = mock_paths / "p1_test.json"
    file.write_text(json.dumps([{"variant": None}]))

    json_to_db.json_to_dir()

    assert any(
        "Skipping malformed entry" in msg
        for level, msg in mock_logger
    )


def test_missing_uid_skips_variant(mock_paths, mock_logger):
    """
    Verify variants without ClinVar UIDs are skipped.
    """
    file = mock_paths / "p1_test.json"
    file.write_text(
        json.dumps(
            [{"variant": "v1", "g_hgvs": "g.1A>T", "esummary": {}}]
        )
    )

    json_to_db.json_to_dir()

    assert any(
        "No ClinVar UID found" in msg
        for level, msg in mock_logger
    )


def test_uid_not_found_in_summary(mock_paths, mock_logger):
    """
    Verify missing UID keys inside the esummary block are detected.
    """
    file = mock_paths / "p1_test.json"
    file.write_text(
        json.dumps(
            [{
                "variant": "v1",
                "g_hgvs": "g.1A>T",
                "esummary": {"uids": ["1"]},
            }]
        )
    )

    json_to_db.json_to_dir()

    assert any(
        "ClinVar UID 1 not found" in msg
        for level, msg in mock_logger
    )


def test_valid_variant_successful_insert(
    mock_paths,
    mock_inserts,
    mock_logger,
):
    """
    Verify a valid variant results in successful DB insert calls.
    """
    file = mock_paths / "p123_wes.json"
    file.write_text(json.dumps([make_valid_variant()]))

    json_to_db.json_to_dir()

    assert len(mock_inserts["patient"]) == 1
    assert len(mock_inserts["variant"]) == 1
    assert len(mock_inserts["clinvar"]) == 1

    clinvar = mock_inserts["clinvar"][0]

    # Validate extracted ClinVar fields
    assert clinvar["gene"] == "BRCA1"
    assert clinvar["chromosome"] == "17"
    assert clinvar["allele_frequency"] == 0.001
    assert "⭐" in clinvar["star_rating"]

    assert any(
        "Inserted variant" in msg
        for level, msg in mock_logger
    )


def test_invalid_allele_frequency_logs_warning(
    mock_paths,
    mock_inserts,
    mock_logger,
):
    """
    Verify invalid allele frequencies are handled gracefully.
    """
    file = mock_paths / "p1_test.json"
    file.write_text(
        json.dumps([make_valid_variant(af="not_a_number")])
    )

    json_to_db.json_to_dir()

    assert any(
        "Invalid allele frequency" in msg
        for level, msg in mock_logger
    )
    assert mock_inserts["clinvar"][0]["allele_frequency"] is None


def test_database_insertion_failure_is_caught(
    mock_paths,
    monkeypatch,
    mock_logger,
):
    """
    Verify database insertion errors are logged and do not crash.
    """
    file = mock_paths / "p1_test.json"
    file.write_text(json.dumps([make_valid_variant()]))

    def fail(*args, **kwargs):
        raise RuntimeError("db down")

    monkeypatch.setattr(
        json_to_db,
        "insert_patient_information",
        fail,
    )

    json_to_db.json_to_dir()

    assert any(
        "Database insertion failed" in msg
        for level, msg in mock_logger
    )


def test_missing_review_status_defaults_to_zero_stars(
    mock_paths,
    mock_inserts,
):
    """
    Verify missing review status results in an 'Unknown' star rating.
    """
    variant = make_valid_variant(review_status=None)
    file = mock_paths / "p1_test.json"
    file.write_text(json.dumps([variant]))

    json_to_db.json_to_dir()

    star_rating = mock_inserts["clinvar"][0]["star_rating"]
    assert star_rating.startswith("Unknown")


