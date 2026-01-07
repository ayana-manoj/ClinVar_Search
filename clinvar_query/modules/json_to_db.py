"""

*********** CREATED WITH THE HELP OF CHATGPT ***********

Process ClinVar JSON result files and insert annotated variant data
into the database.

This script:
- Reads ClinVar JSON files from a configured directory
- Extracts variant, HGNC gene symbol, consensus classification,
  associated conditions, star rating, and allele frequency
- Normalises ClinVar review status into star ratings
- Inserts patient, variant, and ClinVar records into the database
- Logs progress, warnings, and errors using a rotating file logger

All logging is handled via the shared ClinVar_Search_logger.
"""

from pathlib import Path
import json
from decimal import Decimal

from clinvar_query.utils.paths import database_file, clinvar_folder
from clinvar_query.modules.insert_annotated_results import (
    insert_clinvar,
    insert_patient_information,
    insert_variants
)

# Project-wide configured logger (rotating file + console warnings)
from clinvar_query.utils.logger import logger


def json_to_dir():
    """
    Process all ClinVar JSON files in the configured directory.

    For each JSON file:
    - Load ClinVar esummary data
    - Extract relevant annotation fields per variant
    - Safely handle missing or malformed records
    - Insert structured data into the database

    The function logs:
    - INFO: normal progress and successful insertions
    - WARNING: recoverable issues (missing fields, skipped entries)
    - ERROR/EXCEPTION: failures during parsing or database insertion
    """
    # Resolve the directory containing ClinVar JSON files
    json_dir = Path(clinvar_folder)

    # Collect all JSON files in the directory
    json_files = list(json_dir.glob("*.json"))

    # Exit early if no files are found
    if not json_files:
        logger.warning("No JSON files found in %s", json_dir)
        return

    logger.info("Found %d JSON files in %s", len(json_files), json_dir)

    # ------------------------------------------------------------------
    # Process each JSON file independently to avoid cascading failures
    # ------------------------------------------------------------------
    for json_file in json_files:
        logger.info("Processing file: %s", json_file.name)

        try:
            # Load JSON content from file
            with open(json_file, "r") as f:
                variants_data = json.load(f)

            # File naming convention:
            #   <patient_id>_<test_type>.json
            p_id = json_file.stem
            patient_id = p_id.split("_")[0]

        except Exception:
            # Log full traceback for unexpected file parsing errors
            logger.exception("Failed to load JSON file: %s", json_file)
            continue

        # --------------------------------------------------------------
        # Iterate through each variant entry in the JSON payload
        # --------------------------------------------------------------
        for entry in variants_data:
            variant_str = entry.get("variant")
            g_hgvs = entry.get("g_hgvs")
            summary = entry.get("esummary")

            # Skip entries missing critical information
            if not variant_str or not g_hgvs or not isinstance(summary, dict):
                logger.warning(
                    "Skipping malformed entry in %s: %s",
                    json_file.name,
                    entry
                )
                continue

            # ----------------------------------------------------------
            # Resolve ClinVar UID to the full ClinVar record
            # ----------------------------------------------------------
            uids = summary.get("uids")
            if not uids:
                logger.warning(
                    "No ClinVar UID found for variant %s",
                    variant_str
                )
                continue

            uid = uids[0]
            cv_data = summary.get(uid)

            if not cv_data:
                logger.error(
                    "ClinVar UID %s not found in esummary for variant %s",
                    uid,
                    variant_str
                )
                continue

            # ----------------------------------------------------------
            # Extract gene symbol (first gene only)
            # ----------------------------------------------------------
            gene = None
            genes = cv_data.get("genes", [])
            if genes:
                gene = genes[0].get("symbol")

            # ----------------------------------------------------------
            # Determine chromosome from current genome assembly
            # ----------------------------------------------------------
            chromosome = None
            variation_set = cv_data.get("variation_set", [])
            if variation_set:
                for loc in variation_set[0].get("variation_loc", []):
                    # Prefer current assembly coordinates only
                    if loc.get("status") == "current":
                        chromosome = loc.get("chr")
                        break

            # ----------------------------------------------------------
            # Germline classification and review status
            # ----------------------------------------------------------
            germline = cv_data.get("germline_classification", {})

            classification = germline.get("description")
            review_status = germline.get("review_status")

            # Mapping of ClinVar review status text to star rating
            review_to_stars = {
                "no assertion": 0,
                "criteria provided, single submitter": 1,
                "criteria provided, multiple submitters, no conflicts": 2,
                "reviewed by expert panel": 3,
                "practice guideline": 4,
            }

            # Default to zero stars if no review status is available
            stars_count = 0
            if review_status:
                review_norm = review_status.strip().lower()
                for key, value in review_to_stars.items():
                    if key in review_norm:
                        stars_count = value
                        break

            # Human-readable star representation
            stars_visual = "⭐" * stars_count + "☆" * (4 - stars_count)
            star_rating = (
                f"{review_status} ({stars_visual})"
                if review_status
                else f"Unknown ({stars_visual})"
            )

            # ----------------------------------------------------------
            # Extract associated disease/phenotype names
            # ----------------------------------------------------------
            conditions = []
            for trait in germline.get("trait_set", []):
                name = trait.get("trait_name")
                if name:
                    conditions.append(name)

            associated_conditions = (
                "; ".join(conditions) if conditions else None
            )

            # ----------------------------------------------------------
            # Extract gnomAD allele frequency (if present)
            # ----------------------------------------------------------
            allele_frequency = None
            if variation_set:
                freq_set = variation_set[0].get("allele_freq_set", [])
                for freq in freq_set:
                    # Restrict to gnomAD-derived frequencies only
                    source = freq.get("source", "").lower()
                    if "gnomad" in source:
                        value = freq.get("value")
                        try:
                            allele_frequency = (
                                float(value) if value is not None else None
                            )
                        except (ValueError, TypeError):
                            logger.warning(
                                "Invalid allele frequency for variant %s: %s",
                                variant_str,
                                value
                            )
                            allele_frequency = None
                        break

            # Decimal formatting for logging readability
            allele_frequency_decimal = (
                Decimal(str(allele_frequency))
                if allele_frequency is not None else None
            )
            allele_frequency_str = (
                format(allele_frequency_decimal.normalize(), "f")
                if allele_frequency_decimal is not None else "None found"
            )

            # ----------------------------------------------------------
            # Prepare database insertion payloads
            # ----------------------------------------------------------
            clinvar = {
                "variant_id": variant_str,
                "consensus_classification": classification,
                "hgvs": g_hgvs,
                "associated_conditions": associated_conditions,
                "gene": gene,
                "star_rating": star_rating,
                "allele_frequency": allele_frequency_str,
                "chromosome": chromosome,
            }

            patient_info = {
                "patient_id": patient_id
            }

            variants = {
                "variant_id": variant_str,
                "patient_id": patient_id,
                "patient_variant": f"{patient_id} _ ({variant_str})",
            }

            # ----------------------------------------------------------
            # Insert records into the database
            # ----------------------------------------------------------
            try:
                insert_patient_information(patient_info)
                insert_variants(variants)
                insert_clinvar(clinvar)

                logger.info(
                    "Inserted variant %s | classification=%s | review=%s "
                    "| gnomAD_AF=%s",
                    variant_str,
                    classification,
                    star_rating,
                    allele_frequency_str,
                )

            except Exception:
                # Log traceback but continue processing remaining variants
                logger.exception(
                    "Database insertion failed for variant %s",
                    variant_str
                )

    logger.info("All ClinVar JSON files processed successfully.")


if __name__ == "__main__":
    json_to_dir()