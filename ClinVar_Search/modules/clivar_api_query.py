"""
clinvar_variant_query.py
------------------------
This script queries the NCBI ClinVar API to find variant information
based on chromosome number, genomic position, and nucleotide change.

It uses NCBI’s E-utilities (ESearch + ESummary) to search ClinVar data.

Now includes:
- MANE transcript(s)
- ClinVar star ratings (review status)

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
    # Build search term (ClinVar supports chr:posChange, e.g., "7:140453136C>T")
    search_term = f"{chrom}:{position}{change}"

    # ESearch endpoint to find ClinVar IDs
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

    # Retrieve the first ClinVar ID
    id_list = data.get("esearchresult", {}).get("idlist", [])
    if not id_list:
        print("❌ No variant found in ClinVar for that query.")
        return None

    clinvar_id = id_list[0]
    print(f"✅ Found ClinVar ID: {clinvar_id}")

    # Use ESummary to retrieve detailed variant info
    esummary_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
    esummary_params = {
        "db": "clinvar",
        "id": clinvar_id,
        "retmode": "json"
    }

    summary_response = requests.get(esummary_url, params=esummary_params)
    summary_response.raise_for_status()
    summary_data = summary_response.json()

    # Extract main result
    result = summary_data.get("result", {}).get(clinvar_id, {})
    return result


def extract_star_rating(review_status: str) -> str:
    """
    Convert ClinVar review status into star rating.
    Reference: https://www.ncbi.nlm.nih.gov/clinvar/docs/review_status/

    Returns:
        str: Human-readable star rating (e.g., "★★★ (reviewed by expert panel)")
    """
    if not review_status:
        return "No review status available"

    stars_map = {
        "practice guideline": "★★★★",
        "reviewed by expert panel": "★★★",
        "criteria provided, multiple submitters, no conflicts": "★★",
        "criteria provided, single submitter": "★",
        "no assertion criteria provided": "☆"
    }

    # Find a match in the map (case-insensitive)
    for key, stars in stars_map.items():
        if key.lower() in review_status.lower():
            return f"{stars} ({review_status})"

    return review_status


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

        # Star rating (from review_status)
        review_status = result.get("review_status")
        print(f"Review status: {extract_star_rating(review_status)}")

        # MANE transcripts (if available)
        mane_info = result.get("mane")
        if mane_info:
            mane_transcripts = []
            for item in mane_info:
                if "nucleotide_accession" in item:
                    transcript = f"{item['nucleotide_accession']} ({item.get('nucleotide_version', '')})"
                    mane_transcripts.append(transcript)
            if mane_transcripts:
                print(f"MANE transcripts: {', '.join(mane_transcripts)}")
            else:
                print("MANE transcripts: None found")
        else:
            print("MANE transcripts: None found")

    else:
        print("No variant data retrieved.")


if __name__ == "__main__":
    main()

