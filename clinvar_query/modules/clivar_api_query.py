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
    Search ClinVar for a given HGVS variant and return ClinVar IDs (RCV IDs).

    Parameters
    ----------
    hgvs : str
        HGVS string representing the genomic variant.

    Returns
    -------
    list
        A list of ClinVar RCV IDs matching the HGVS variant.
        Returns an empty list if no IDs are found or an error occurs.
    """
    params = {"db": "clinvar", "term": hgvs, "retmode": "json"}
    try:
        response = requests.get(ESEARCH_URL, params=params)
        response.raise_for_status()
        data = response.json()
        # Extract list of ClinVar IDs from the JSON response
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
        Returns an empty dictionary if no IDs are provided or an error occurs.
    """
    if not clinvar_ids:
        return {}

    params = {"db": "clinvar", "id": ",".join(clinvar_ids), "retmode": "json"}
    try:
        response = requests.get(ESUMMARY_URL, params=params)
        response.raise_for_status()
        return response.json().get("result", {})
    except Exception as e:
        logger.error(f"Error getting esummary for IDs {clinvar_ids}: {e}")
        return {}


# ----------------- Main Processing -----------------
# Define input and output directories
input_dir = "vv_search_output_files"
output_dir = "clinvar_results"
os.makedirs(output_dir, exist_ok=True)

# List all JSON files in the input directory
json_files = list(Path(input_dir).glob("*.json"))
if not json_files:
    logger.warning(f"No JSON files found in directory {input_dir}")

# Iterate over each JSON file
for input_file in json_files:
    logger.info(f"Processing file: {input_file.name}")

    # Load variant data from JSON file
    try:
        with open(input_file) as f:
            variants_data = json.load(f)
    except Exception as e:
        logger.error(f"Failed to load JSON file {input_file}: {e}")
        continue

    results = []

    # Iterate over each variant entry in the JSON file
    for entry in variants_data:
        variant_str = entry.get("variant")
        if not variant_str:
            logger.warning("Variant entry missing 'variant' field, skipping.")
            continue

        # Extract the g_hgvs notation from the nested structure
        try:
            variant_result = entry["result"][variant_str][variant_str]
            g_hgvs = variant_result.get("g_hgvs")
        except KeyError:
            g_hgvs = None

        if not g_hgvs:
            logger.warning(f"No g_hgvs found for {variant_str}, skipping.")
            continue

        # Search ClinVar using HGVS notation
        logger.info(f"Searching ClinVar for HGVS: {g_hgvs}")
        clinvar_ids = search_clinvar(g_hgvs)
        summary = get_esummary(clinvar_ids)

        # Append results to the output list
        results.append({
            "variant": variant_str,
            "g_hgvs": g_hgvs,
            "clinvar_ids": clinvar_ids,
            "esummary": summary
        })

        # Respect NCBI API guidelines by adding a small delay
        time.sleep(0.3)

    # Save results to output directory with the same filename
    output_file = Path(output_dir) / input_file.name
    try:
        with open(output_file, "w") as f:
            json.dump(results, f, indent=2)
        logger.info(f"Results saved to {output_file}")
    except Exception as e:
        logger.error(f"Failed to save results for {input_file.name}: {e}")

logger.info("All files processed successfully.")


