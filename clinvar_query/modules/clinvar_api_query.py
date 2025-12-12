"""
*********** CREATED USING CHATGPT ***********

clinvar_api_query.py

This module provides functionality to query the NCBI ClinVar database using
HGVS variant notation. It supports searching for ClinVar RCV IDs and fetching
esummary information. Additionally, it includes processing logic to handle
JSON input files, query ClinVar for each variant, and save results to output
files.

Functions
---------
search_clinvar(hgvs: str) -> list
    Search ClinVar for a given HGVS variant and return a list of ClinVar IDs.

get_esummary(clinvar_ids: list) -> dict
    Fetch esummary information from ClinVar for a list of ClinVar IDs.

process_files(input_dir: str, output_dir: str)
    Process all JSON files in an input directory, query ClinVar for each variant,
    and save results to an output directory.
"""

import json
import requests
import time
import os
from pathlib import Path
from clinvar_query.logger import logger

# ----------------- NCBI E-utilities URLs -----------------
ESUMMARY_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
ESEARCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"


# ----------------- Functions -----------------
def search_clinvar(hgvs: str) -> list:
    """
    Search ClinVar for a given HGVS variant and return a list of ClinVar RCV IDs.

    Parameters
    ----------
    hgvs : str
        HGVS string representing the genomic variant (e.g., "NM_000546.5:c.215C>G").

    Returns
    -------
    list
        A list of ClinVar RCV IDs matching the HGVS variant.
        Returns an empty list if no IDs are found or if an error occurs.
    """
    params = {"db": "clinvar", "term": hgvs, "retmode": "json"}

    try:
        # Send GET request to ClinVar ESearch endpoint
        response = requests.get(ESEARCH_URL, params=params)
        response.raise_for_status()

        # Parse JSON response
        data = response.json()
        return data.get("esearchresult", {}).get("idlist", [])

    except Exception as e:
        logger.error(f"Error searching ClinVar for {hgvs}: {e}")
        return []


def get_esummary(clinvar_ids: list) -> dict:
    """
    Fetch ClinVar esummary information for a list of ClinVar IDs.

    Parameters
    ----------
    clinvar_ids : list
        List of ClinVar RCV IDs to fetch summaries for.

    Returns
    -------
    dict
        JSON dictionary containing the ClinVar esummary results.
        Returns an empty dictionary if no IDs are provided or if an error occurs.
    """
    if not clinvar_ids:
        # Return empty dictionary if no IDs are provided
        return {}

    params = {"db": "clinvar", "id": ",".join(clinvar_ids), "retmode": "json"}

    try:
        # Send GET request to ClinVar ESummary endpoint
        response = requests.get(ESUMMARY_URL, params=params)
        response.raise_for_status()

        # Return the "result" section from the JSON response
        return response.json().get("result", {})

    except Exception as e:
        logger.error(f"Error getting esummary for IDs {clinvar_ids}: {e}")
        return {}


# ----------------- Processing Logic -----------------
def process_files(input_dir: str, output_dir: str):
    """
    Process all JSON files in the input directory, query ClinVar for each variant,
    and save results to the output directory.

    Parameters
    ----------
    input_dir : str
        Path to the directory containing input JSON files with variant information.

    output_dir : str
        Path to the directory where output JSON files will be saved.

    Notes
    -----
    - Each input JSON file should contain a list of dictionaries, each representing
      a variant with "variant" and "result" keys.
    - Variants missing the "variant" key or "g_hgvs" notation are skipped.
    """
    # Ensure the output directory exists
    os.makedirs(output_dir, exist_ok=True)

    # List all JSON files in the input directory
    json_files = list(Path(input_dir).glob("*.json"))

    if not json_files:
        logger.warning(f"No JSON files found in directory {input_dir}")
        return

    # Process each JSON input file
    for input_file in json_files:
        logger.info(f"Processing file: {input_file.name}")

        # Load JSON content from the input file
        try:
            with open(input_file) as f:
                variants_data = json.load(f)
        except Exception as e:
            logger.error(f"Failed to load JSON file {input_file}: {e}")
            continue

        results = []

        # Process each variant entry
        for entry in variants_data:
            variant_str = entry.get("variant")
            if not variant_str:
                logger.warning("Variant entry missing 'variant' field, skipping.")
                continue

            # Attempt to extract the g_hgvs notation from nested structure
            try:
                variant_result = entry["result"][variant_str][variant_str]
                g_hgvs = variant_result.get("g_hgvs")
            except KeyError:
                g_hgvs = None

            if not g_hgvs:
                logger.warning(f"No g_hgvs found for {variant_str}, skipping.")
                continue

            # Query ClinVar
            logger.info(f"Searching ClinVar for HGVS: {g_hgvs}")
            clinvar_ids = search_clinvar(g_hgvs)
            summary = get_esummary(clinvar_ids)

            # Append results for this variant
            results.append({
                "variant": variant_str,
                "g_hgvs": g_hgvs,
                "clinvar_ids": clinvar_ids,
                "esummary": summary
            })

            # Respect NCBI API guidelines by adding a small delay
            time.sleep(0.3)

        # Save results to the output directory
        output_file = Path(output_dir) / input_file.name
        try:
            with open(output_file, "w") as f:
                json.dump(results, f, indent=2)
            logger.info(f"Results saved to {output_file}")
        except Exception as e:
            logger.error(f"Failed to save results for {input_file.name}: {e}")

    logger.info("All files processed successfully.")


# ----------------- CLI Entry -----------------
if __name__ == "__main__":
    # Default input/output directories if running as a script
    process_files("vv_search_output_files", "clinvar_results")

