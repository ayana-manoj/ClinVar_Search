"""

*********** DEVELOPED WITH CHATGPT ASSISTANCE ***********

Database insertion utilities for ClinVar query results.

This module provides helper functions to insert or update records
related to:
- Patient metadata
- Patient–variant associations
- ClinVar annotations

Logging is handled by the shared ClinVar logger, which must be
configured elsewhere in the application.
"""

#Developed with the aid of CHATGPT

import sqlite3

from clinvar_query.utils.paths import database_file
from clinvar_query.utils.logger import logger

from clinvar_query.utils.paths import database_file
from clinvar_query.utils.logger import logger


def insert_patient_information(data):
    """
        Insert or update patient information in the database.

        Parameters
        ----------
        data : dict
            Dictionary containing patient metadata with the following keys:

            patient_id : str
                Unique identifier for the patient.

        Notes
        -----
        - Uses ``INSERT OR IGNORE`` to ensure idempotent behavior.
        - Allows safe re-processing of identical patient records without
          raising integrity errors.
        """
    logger.debug("Preparing to insert patient information: %s", data)

    try:
        # Establish a connection to the SQLite database
        con = sqlite3.connect(database_file)
        cursor = con.cursor()

        # Insert patient information if it does not already exist
        cursor.execute(
            """
            INSERT OR IGNORE INTO patient_information
            (patient_id)
            VALUES (?)
            """,
            (
                data.get("patient_id"),
            ),
        )

        # Commit the transaction to persist changes
        con.commit()

        logger.info(
            "Inserted/Updated patient information: %s",
            data.get("patient_id"),
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
       Insert or update patient–variant association records.

       Parameters
       ----------
       data : dict
           Dictionary containing variant association data with the
           following keys:

           variant_id : str
               Unique identifier for the variant.

           patient_id : str
               Identifier for the associated patient.

           patient_variant : str
               Composite identifier linking patient and variant.
       """
    logger.debug("Preparing to insert variant record: %s", data)

    try:
        # Open a database connection
        con = sqlite3.connect(database_file)
        cursor = con.cursor()
        # Insert the patient–variant association if absent
        cursor.execute(
            """
            INSERT OR IGNORE INTO variants
            (variant_id, patient_id, patient_variant)
            VALUES (?, ?, ?)
            """,
            (
                data.get("variant_id"),
                data.get("patient_id"),
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
            INSERT OR IGNORE INTO clinvar
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
                data.get("allele_frequency"),
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