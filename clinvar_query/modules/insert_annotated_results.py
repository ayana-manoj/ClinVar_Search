"""
Database insertion utilities for ClinVar query results.

This module provides helper functions to insert or update:
- Patient information
- Variant associations
- ClinVar annotations

Logging is handled by the shared ClinVar_Search_logger, which must be
configured elsewhere in the application.
"""

import sqlite3

from clinvar_query.utils.paths import database_file
from clinvar_query.logger import logger


def insert_patient_information(data):
    """
    Insert or update a patient's information into the database.

    Parameters
    ----------
    data : dict
        Dictionary containing:
        - patient_id (str): Unique patient identifier
        - id_test_type (str): Identifier for the test or assay

    Notes
    -----
    Uses INSERT OR REPLACE to ensure idempotent behaviour and allow
    re-processing of the same patient data.
    """
    logger.debug("Preparing to insert patient information: %s", data)

    try:
        # Establish a connection to the SQLite database
        con = sqlite3.connect(database_file)
        cursor = con.cursor()

        # Insert or replace patient information
        cursor.execute(
            """
            INSERT OR REPLACE INTO patient_information
            (patient_id, id_test_type)
            VALUES (?, ?)
            """,
            (
                data.get("patient_id"),
                data.get("id_test_type"),
            ),
        )

        # Commit the transaction to persist changes
        con.commit()

        logger.info(
            "Inserted/Updated patient information: %s",
            data.get("id_test_type"),
        )

    except sqlite3.DatabaseError:
        # Log database errors with full traceback
        logger.exception(
            "Failed to insert patient information: %s", data
        )
        raise

    finally:
        # Always close the database connection
        con.close()


def insert_variants(data):
    """
    Insert or update variant information in the database.

    Parameters
    ----------
    data : dict
        Dictionary containing:
        - variant_id (str): Variant identifier
        - id_test_type (str): Test identifier
        - patient_variant (str): Composite patient-variant key
    """
    logger.debug("Preparing to insert variant record: %s", data)

    try:
        con = sqlite3.connect(database_file)
        cursor = con.cursor()

        cursor.execute(
            """
            INSERT OR REPLACE INTO variants
            (variant_id, id_test_type, patient_variant)
            VALUES (?, ?, ?)
            """,
            (
                data.get("variant_id"),
                data.get("id_test_type"),
                data.get("patient_variant"),
            ),
        )

        con.commit()

        logger.info(
            "Inserted/Updated variant association: %s",
            data.get("patient_variant"),
        )

    except sqlite3.DatabaseError:
        logger.exception(
            "Failed to insert variant record: %s", data
        )
        raise

    finally:
        con.close()


def insert_clinvar(data):
    """
    Insert or update ClinVar variant information into the database.

    Parameters
    ----------
    data : dict
        Dictionary containing:
        - variant_id (str)
        - hgvs (str)
        - associated_conditions (str or None)
        - gene (str or None)
        - chromosome (str or None)
        - consensus_classification (str or None)
        - star_rating (str)
        - allele_frequency (float or None)

    Notes
    -----
    Allele frequency is explicitly coerced to a float (or None)
    to avoid SQLite type ambiguity.
    """
    logger.debug("Preparing to insert ClinVar record: %s", data)

    # Safely coerce allele frequency to float
    af = data.get("allele_frequency")
    try:
        allele_frequency = float(af) if af is not None else None
    except (ValueError, TypeError):
        logger.warning(
            "Invalid allele frequency for variant %s: %s",
            data.get("variant_id"),
            af,
        )
        allele_frequency = None

    try:
        con = sqlite3.connect(database_file)
        cursor = con.cursor()

        cursor.execute(
            """
            INSERT OR REPLACE INTO clinvar
            (
                variant_id,
                hgvs,
                associated_conditions,
                chromosome,
                gene,
                consensus_classification,
                star_rating,
                allele_frequency
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                data.get("variant_id"),
                data.get("hgvs"),
                data.get("associated_conditions"),
                data.get("chromosome"),
                data.get("gene"),
                data.get("consensus_classification"),
                data.get("star_rating"),
                allele_frequency,
            ),
        )

        con.commit()

        logger.info(
            "Inserted/Updated ClinVar record: %s",
            data.get("variant_id"),
        )

    except sqlite3.DatabaseError:
        logger.exception(
            "Failed to insert ClinVar record: %s", data
        )
        raise

    finally:
        con.close()
