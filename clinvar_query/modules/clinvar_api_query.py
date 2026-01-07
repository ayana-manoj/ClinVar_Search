"""

*********** CHATGPT USED IN THE CREATION OF THIS MODULE ***********

ClinVar query and annotation pipeline.

This module queries the NCBI ClinVar database using HGVS variant strings,
retrieves matching ClinVar record identifiers (RCV IDs), and fetches
summary metadata via the NCBI E-utilities API.

Input variants are read from JSON files produced by a prior validation
step, and results are written to a corresponding output directory.

Notes
-----
- NCBI E-utilities usage guidelines are respected by throttling requests.
- Network or parsing errors are logged and handled gracefully.
"""

import json
import requests
import time
import os
from pathlib import Path
from clinvar_query.utils.logger import logger
from clinvar_query.utils.paths import validator_folder, clinvar_folder

# ----------------- NCBI E-utilities URLs -----------------
# Base endpoints for searching ClinVar and retrieving summary metadata
ESUMMARY_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
ESEARCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"


# ----------------- Functions -----------------
def search_clinvar(hgvs: str) -> list:
    ESUMMARY_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
    ESEARCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    """
        Search ClinVar for a given HGVS variant string.

        This function queries the NCBI ESearch API against the ClinVar
        database and returns a list of matching ClinVar record IDs (RCVs).

        Parameters
        ----------
        hgvs : str
            HGVS string representing a genomic variant (e.g., g.HGVS).

        Returns
        -------
        list of str
            List of ClinVar RCV IDs matching the HGVS query.
            Returns an empty list if no matches are found or an error occurs.

        Notes
        -----
        - This function performs a network request and may raise latency.
        - Errors are logged but not propagated to allow batch processing.
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
    ESUMMARY_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"

    """
        Retrieve ClinVar summary metadata for a list of ClinVar IDs.

        This function queries the NCBI ESummary API and returns summary
        information for each supplied ClinVar RCV identifier.

        Parameters
        ----------
        clinvar_ids : list of str
            List of ClinVar RCV IDs to retrieve summaries for.

        Returns
        -------
        dict
            Dictionary containing the ESummary results keyed by ClinVar ID.
            Returns an empty dictionary if no IDs are provided or an error occurs.

        Notes
        -----
        - If `clinvar_ids` is empty, the API call is skipped.
        - Errors are logged but do not interrupt processing.
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

def process_clinvar(input_dir, output_dir):
    """
        Process validated variant JSON files and annotate them with ClinVar data.

        For each input JSON file:
        - Extract g.HGVS notations for each variant
        - Query ClinVar for matching RCV IDs
        - Fetch summary metadata for each RCV
        - Write results to a corresponding output JSON file

        Parameters
        ----------
        input_dir : str or pathlib.Path
            Directory containing validated variant JSON files.
        output_dir : str or pathlib.Path
            Directory where ClinVar-annotated JSON files will be written.

        Notes
        -----
        - Files already present in the output directory are skipped.
        - A small delay is inserted between API calls to comply with
          NCBI rate-limiting recommendations.
        """
    # ----------------- Main Processing -----------------
    # Define input and output directories
    ESEARCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    ESUMMARY_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"

    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)

    # List all JSON files in the input directory
    json_files = list(Path(input_dir).glob("*.json"))
    if not json_files:
        logger.warning(f"No JSON files found in directory {input_dir}")
    # look at all output files 
    output_files = list(Path(output_dir).glob("*json"))
    output_basenames = {f.stem for f in output_files}
    

    # Iterate over each JSON file
    for input_file in json_files:
        if input_file.stem in output_basenames:
            logger.warning(f"skipping already processed file: {input_file.name}")
            continue
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

if __name__ == "__main__":

    process_clinvar(validator_folder, clinvar_folder)