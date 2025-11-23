"""
lovd_hgvs_query.py
------------------------
Reads VCF-style variants from a TXT file and queries the LOVD API
to retrieve the best HGVS description.

Returns:
    - transcript HGVS (preferred: c. or p.)
    - genomic HGVS (fallback)
    - confidence score
"""

import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any, Tuple, Optional
from pathlib import Path


# ---------------------------------------------------
# Read variants from TXT file
# ---------------------------------------------------
def read_variants_from_txt(txt_file: str | Path) -> List[str]:
    """
    Load variants from a TXT file in the format:
        chrom-pos-ref-alt

    Returns:
        List of variant strings.
    """
    txt_file = Path(txt_file)
    if not txt_file.exists():
        raise FileNotFoundError(f"Variant file not found: {txt_file}")

    variants = []

    with txt_file.open() as f:
        for line in f:
            variant = line.strip()
            if not variant or variant.startswith("#"):
                continue

            parts = variant.split("-")
            if len(parts) != 4:
                print(f"⚠️ Skipping invalid variant: {variant}")
                continue

            variants.append(variant)

    print(f"📌 Loaded {len(variants)} variants from {txt_file}")
    return variants


# ---------------------------------------------------
# Query LOVD API
# ---------------------------------------------------
def query_lovd(vcf_variant: str) -> Dict[str, Any]:
    """
    Query LOVD and return best transcript HGVS if available.

    Args:
        vcf_variant (str): "chrom-pos-ref-alt"

    Returns:
        dict with:
            - transcript_hgvs
            - genomic_hgvs
            - best_confidence
            - raw LOVD data
    """
    url = f"https://api.lovd.nl/checkHGVS/{requests.utils.quote(vcf_variant, safe='')}"

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        return {
            "variant": vcf_variant,
            "transcript_hgvs": None,
            "genomic_hgvs": None,
            "confidence": None,
            "error": str(e),
        }

    items = data.get("data", [])
    if not items or "corrected_values" not in items[0]:
        return {
            "variant": vcf_variant,
            "transcript_hgvs": None,
            "genomic_hgvs": None,
            "confidence": None,
            "error": "No corrected_values returned",
        }

    corrected = items[0]["corrected_values"]

    # Prefer transcript HGVS (c. or p.)
    transcript_candidates = {k: v for k, v in corrected.items() if "c." in k or "p." in k}

    if transcript_candidates:
        best = max(transcript_candidates, key=lambda k: transcript_candidates[k])
        confidence = transcript_candidates[best]
        transcript_hgvs = best
    else:
        # fallback to highest-confidence HGVS (likely genomic)
        best = max(corrected, key=lambda k: corrected[k])
        confidence = corrected[best]
        transcript_hgvs = None

    # extract genomic HGVS (g.)
    genomic_candidates = [k for k in corrected if ":g." in k]
    genomic_hgvs = genomic_candidates[0] if genomic_candidates else None

    return {
        "variant": vcf_variant,
        "transcript_hgvs": transcript_hgvs,
        "genomic_hgvs": genomic_hgvs,
        "confidence": confidence,
        "raw": data,
    }


# ---------------------------------------------------
# Parallel processor
# ---------------------------------------------------
def process_variants_parallel(
    variants: List[str],
    threads: int = 8
) -> List[Dict[str, Any]]:
    """
    Perform LOVD queries in parallel.

    Returns:
        List of dictionaries with HGVS output.
    """
    results = []

    with ThreadPoolExecutor(max_workers=threads) as executor:
        future_map = {executor.submit(query_lovd, v): v for v in variants}

        for fut in as_completed(future_map):
            v = future_map[fut]
            try:
                results.append(fut.result())
            except Exception as e:
                results.append({
                    "variant": v,
                    "transcript_hgvs": None,
                    "genomic_hgvs": None,
                    "confidence": None,
                    "error": str(e),
                })

    return results







