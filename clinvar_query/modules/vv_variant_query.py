"""
VariantValidator Batch Query Script
-----------------------------------

This script reads variant descriptions from one or more text files,
queries the VariantValidator API for each variant, and writes the
API results to a JSON file. Each input `.txt` file produces its own
output `.json` file with the same name.

Features
--------
- Automatically discovers all input files matching a wildcard pattern.
- Queries the VariantValidator API for each variant line.
- Stores results (success or error) in a structured JSON file.
- Ensures output directory exists before writing.
- Uses clear error responses to help with troubleshooting.
"""

import os
import glob
import json
import requests
from clinvar_query.logger import logger

# ----------------- Configuration -----------------
input_file_pattern = "Clinvar_Search_Output_Files/*.txt"
output_folder = "vv_search_output_files"

base_url = "https://rest.variantvalidator.org/VariantFormatter/variantformatter"
build = "GRCh38"
model = "refseq"
transcript = "mane_select"
checkonly = "False"


# ----------------- Variant Query Function -----------------
def vv_variant_query():
    """
    Reads variants from input files, sends each variant to the
    VariantValidator API, and stores all results in JSON output files.

    Workflow
    --------
    1. Ensure the output directory exists.
    2. Locate all input `.txt` files.
    3. For each file:
        a. Read variants line-by-line.
        b. Query VariantValidator for each variant.
        c. Store results in a list (success or error).
        d. Write results to a JSON file using the same filename.
    """
    # Ensure output directory exists
    os.makedirs(output_folder, exist_ok=True)
    logger.info(f"Output folder verified/created: {output_folder}")

    # Locate input files
    files = glob.glob(input_file_pattern)
    if not files:
        logger.warning(f"No input files found matching pattern: {input_file_pattern}")
        return

    logger.info(f"Found {len(files)} input file(s) to process.")

    # Process each input file
    for file in files:
        input_filename = os.path.basename(file)
        logger.info(f"Processing file: {input_filename}")

        # Read variants from file
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
                    results.append({
                        "variant": variant,
                        "result": response.json()
                    })
                    logger.debug(f"Successfully retrieved result for variant: {variant}")
                else:
                    results.append({
                        "variant": variant,
                        "error": f"Failed to retrieve data ({response.status_code})"
                    })
                    logger.warning(f"Variant {variant} returned status code {response.status_code}")
            except Exception as e:
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


