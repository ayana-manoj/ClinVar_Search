"""
clinvar_api_query.py
------------------------
Query ClinVar using HGVS **c. notation**, with caching.
Returns conditions, classification, star rating, etc.

This script expects HGVS c. strings with transcript, e.g.:
    NM_000059.4:c.7397C>T
"""

import requests
from diskcache import Cache
from pathlib import Path

# Persistent cache directory
CACHE_DIR = Path(__file__).resolve().parent / "cache"
CACHE_DIR.mkdir(exist_ok=True)
cache = Cache(CACHE_DIR)


# -------------------------------------------------------------------
# Convert ClinVar review status → star rating
# -------------------------------------------------------------------
def extract_star_rating(review_status: str) -> str:
    """Convert ClinVar review_status to readable star rating."""
    if not review_status:
        return "No review status available"

    stars_map = {
        "practice guideline": "★★★★",
        "reviewed by expert panel": "★★★",
        "criteria provided, multiple submitters, no conflicts": "★★",
        "criteria provided, single submitter": "★",
        "no assertion criteria provided": "☆"
    }

    review_status_lower = review_status.lower()
    for key, stars in stars_map.items():
        if key.lower() in review_status_lower:
            return f"{stars} ({review_status})"

    return review_status


# -------------------------------------------------------------------
# MAIN FUNCTION: Query ClinVar by HGVS c. notation
# -------------------------------------------------------------------
def query_clinvar_by_hgvs_c(hgvs_c: str) -> dict | None:
    """
    Query ClinVar using an HGVS c. notation string (with transcript), e.g.:

        'NM_000059.4:c.7397C>T'

    ClinVar supports c. HGVS in ESearch queries.

    Returns:
        Dict with classification, conditions, review status, MANE transcripts, etc.
        OR None if not found.
    """

    # Use cache if available
    if hgvs_c in cache:
        return cache[hgvs_c]

    # ------------------------------
    # Step 1) ESearch for ClinVar ID
    # ------------------------------
    esearch_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    esearch_params = {
        "db": "clinvar",
        "term": hgvs_c,
        "retmode": "json"
    }

    try:
        response = requests.get(esearch_url, params=esearch_params, timeout=10)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        print(f"ClinVar ESearch error for {hgvs_c}: {e}")
        return None

    idlist = data.get("esearchresult", {}).get("idlist", [])
    if not idlist:
        cache[hgvs_c] = None
        return None

    clinvar_id = idlist[0]

    # ------------------------------
    # Step 2) Fetch variant summary
    # ------------------------------
    esummary_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
    esummary_params = {
        "db": "clinvar",
        "id": clinvar_id,
        "retmode": "json"
    }

    try:
        summary_response = requests.get(esummary_url, params=esummary_params, timeout=10)
        summary_response.raise_for_status()
        summary = summary_response.json()
    except Exception as e:
        print(f"ClinVar ESummary error for ID {clinvar_id}: {e}")
        return None

    result = summary.get("result", {}).get(clinvar_id, {})
    if not result:
        cache[hgvs_c] = None
        return None

    # ------------------------------
    # Extract output fields
    # ------------------------------
    traits = result.get("trait_set", [])
    conditions = [t.get("trait_name") for t in traits if t.get("trait_name")]

    output = {
        "variation_id": result.get("uid"),
        "title": result.get("title"),
        "clinical_significance": result.get("clinical_significance", {}).get("description"),
        "classification": result.get("clinical_significance", {}).get("description"),
        "review_status": extract_star_rating(result.get("review_status")),
        "conditions": conditions,
        "genes": [g["symbol"] for g in result.get("gene", [])] if result.get("gene") else [],
        "last_updated": result.get("updated"),
        "mane_transcripts": [],
    }

    # MANE transcripts
    mane_data = result.get("mane")
    if mane_data:
        for entry in mane_data:
            if "nucleotide_accession" in entry:
                acc = entry["nucleotide_accession"]
                ver = entry.get("nucleotide_version", "")
                output["mane_transcripts"].append(f"{acc}.{ver}")

    # Save to cache
    cache[hgvs_c] = output

    return output


