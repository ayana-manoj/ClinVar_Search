"""

*********** MODULE DEVELOPED WITH THE AID OF CHATGPT ***********


VariantValidator Batch Query Script
-----------------------------------

This module provides a batch interface for querying the VariantValidator
REST API using variant descriptions stored in text files.

Each input ``.txt`` file is processed line-by-line, with each line
representing a single variant description. Results from the API are
written to a corresponding ``.json`` file with the same base name.

Features
--------
- Discovers all input files matching a wildcard pattern.
- Queries the VariantValidator API for each variant.
- Stores results (success or error) in structured JSON output.
- Ensures output directories exist before writing.
- Logs progress, warnings, and errors for traceability.

Notes
-----
This script is designed to be executed as a standalone module but may
also be imported and invoked programmatically.
"""

import os
import glob
import json
import requests
from clinvar_query.utils.logger import logger
from clinvar_query.utils.paths import processed_folder, validator_folder
from pathlib import Path


# ----------------- Configuration -----------------
#: Wildcard pattern for input variant files.
input_file_pattern = str(processed_folder/"*.txt")
#: Directory where JSON output files will be written.
output_folder = validator_folder
#: Wildcard pattern for existing JSON output files
output_file_pattern = str(output_folder/"*.json")
#: Base URL for the VariantValidator REST API
base_url = "https://rest.variantvalidator.org/VariantFormatter/variantformatter"
#: Genome build to use for variant normalization.
build = "GRCh38"
#: Transcript model to use for variant formatting
model = "refseq"
#: Transcript selection strategy.
transcript = "mane_select"
#: Whether to run the API in "check-only" mode
checkonly = "False"


# ----------------- Variant Query Function -----------------
def vv_variant_query():
    """
        Query VariantValidator for variants listed in input text files.

        This function discovers all matching input files, submits each
        variant description to the VariantValidator API, and writes the
        collected results to JSON files in the configured output directory.

        Workflow
        --------
        1. Ensure the output directory exists.
        2. Locate all input ``.txt`` files.
        3. Identify already-processed files to avoid duplication.
        4. For each unprocessed file:
            a. Read variants line-by-line.
            b. Query VariantValidator for each variant.
            c. Capture success or error responses.
            d. Write results to a JSON file with the same base name.

        Returns
        -------
        None

        Notes
        -----
        - Files with existing JSON outputs are skipped to ensure idempotency.
        - Network or API failures are captured per-variant and logged.
        """

    # Ensure output directory exists
    os.makedirs(output_folder, exist_ok=True)
    logger.info(f"Output folder verified/created: {output_folder}")

#CHANGE ADDED TO HELP WITH TEST (test_vv_variant_query.py)
    # Locate input files
    files = glob.glob(input_file_pattern)
    if not files:
        logger.warning(f"No input files found matching pattern: {input_file_pattern}")
        return

    # Locate output files (SAFE from glob patching)
    output_dir = Path(output_folder)
    output_files = list(output_dir.glob("*.json"))
    output_basenames = {f.stem for f in output_files}

    # ------------------------------------------------------------------
    # Alternative implementation (retained for reference)
    #
    # This approach uses ``glob.glob`` for output discovery but may be
    # affected by glob patching in test environments.
    #
    # files = glob.glob(input_file_pattern)
    # if not files:
    #     logger.warning(
    #         f"No input files found matching pattern: {input_file_pattern}"
    #     )
    #     return
    #
    # output_files = glob.glob(output_file_pattern)
    # output_basenames = {Path(f).stem for f in output_files}
    # ------------------------------------------------------------------


    # Process each input file independently
    for file in files:
        input_filename = os.path.basename(file)
        input_stem = Path(input_filename).stem
        logger.info(f"Processing file: {input_filename}")

        # Skip files that already have corresponding JSON outputs.
        if input_stem in output_basenames:
            logger.warning(f"skipping already processed file: {input_filename}")
            continue

        # Read and sanitize variant entries from the input file.
        try:
            with open(file, "r") as f:
                variants = [line.strip() for line in f if line.strip()]
            logger.info(f"Loaded {len(variants)} variants from {input_filename}")
        except Exception as e:
            logger.error(f"Failed to read file {input_filename}: {e}")
            continue

        results = []

        # Query VariantValidator API for each variant
        for variant in variants:
            url = f"{base_url}/{build}/{variant}/{model}/{transcript}/{checkonly}"
            try:
                response = requests.get(url)
                if response.status_code == 200:
                    # Successful API response
                    results.append({
                        "variant": variant,
                        "result": response.json()
                    })
                    logger.debug(f"Successfully retrieved result for variant: {variant}")
                else:
                    # API responded but returned an error status code
                    results.append({
                        "variant": variant,
                        "error": f"Failed to retrieve data ({response.status_code})"
                    })
                    logger.warning(f"Variant {variant} returned status code {response.status_code}")
            except Exception as e:
                # Network or unexpected failure during request execution
                results.append({
                    "variant": variant,
                    "error": f"Exception during request: {e}"
                })
                logger.error(f"Exception querying variant {variant}: {e}")

        # Write results to JSON file
        output_filename = input_filename.replace(".txt", ".json")
        output_path = os.path.join(output_folder, output_filename)
        try:
            with open(output_path, "w") as out_f:
                json.dump(results, out_f, indent=4)
            logger.info(f"Saved JSON output: {output_path}")
        except Exception as e:
            logger.error(f"Failed to save JSON output for {input_filename}: {e}")


# ----------------- Main Execution -----------------
if __name__ == "__main__":
    logger.info("Starting VariantValidator batch query script.")
    vv_variant_query()
    logger.info("VariantValidator batch query script finished.")