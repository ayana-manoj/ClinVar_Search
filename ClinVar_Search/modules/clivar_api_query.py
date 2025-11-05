"""
clinvar_variant_query.py
------------------------
This script queries the NCBI ClinVar API to find variant information
based on chromosome number, genomic position, and nucleotide change.

It uses NCBI’s E-utilities (ESearch + ESummary) to search ClinVar data.

Example:
    python clinvar_variant_query.py --chrom 7 --position 140453136 --change C>T
"""

import requests
import argparse

def query_clinvar(chrom, position, change):
    """
    Query ClinVar using the chromosome, position, and change.

    Args:
        chrom (str): Chromosome number (e.g., '7')
        position (int): Genomic position (e.g., 140453136)
        change (str): Variant change (e.g., 'C>T')

    Returns:
        dict: ClinVar variant summary information (if found), otherwise None
    """
    # Build search term in a format ClinVar understands.
    # ClinVar supports searching by "chr7:140453136C>T" or similar HGVS expressions.
    search_term = f"{chrom}:{position}{change}"

    # ClinVar ESearch URL (returns a list of matching IDs)
    esearch_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"

    esearch_params = {
        "db": "clinvar",
        "term": search_term,
        "retmode": "json"
    }

    print(f"🔍 Searching ClinVar for: {search_term}")
    response = requests.get(esearch_url, params=esearch_params)
    response.raise_for_status()
    data = response.json()

    # Get ClinVar ID(s)
    id_list = data.get("esearchresult", {}).get("idlist", [])
    if not id_list:
        print("❌ No variant found in ClinVar for that query.")
        return None

    clinvar_id = id_list[0]
    print(f"✅ Found ClinVar ID: {clinvar_id}")

    # Use ESummary to get more details about the variant
    esummary_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
    esummary_params = {
        "db": "clinvar",
        "id": clinvar_id,
        "retmode": "json"
    }

    summary_response = requests.get(esummary_url, params=esummary_params)
    summary_response.raise_for_status()
    summary_data = summary_response.json()

    # Extract and return useful info
    result = summary_data.get("result", {}).get(clinvar_id, {})
    return result


def main():
    parser = argparse.ArgumentParser(description="Query ClinVar for a variant by chromosome, position, and change.")
    parser.add_argument("--chrom", required=True, help="Chromosome number (e.g. '7')")
    parser.add_argument("--position", required=True, type=int, help="Genomic position (e.g. 140453136)")
    parser.add_argument("--change", required=True, help="Nucleotide change (e.g. 'C>T')")

    args = parser.parse_args()

    result = query_clinvar(args.chrom, args.position, args.change)

    if result:
        print("\n=== ClinVar Variant Information ===")
        print(f"Title: {result.get('title')}")
        print(f"Clinical significance: {result.get('clinical_significance', {}).get('description')}")
        print(f"Variation ID: {result.get('uid')}")
        print(f"Gene(s): {', '.join([g['symbol'] for g in result.get('gene', [])]) if result.get('gene') else 'N/A'}")
        print(f"Last updated: {result.get('updated')}")
    else:
        print("No variant data retrieved.")


if __name__ == "__main__":
    main()
