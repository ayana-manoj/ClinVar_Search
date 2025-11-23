"""
mutalyzer_hgvs_query.py
------------------------
Reads VCF-style variants from a TXT file ("chrom-pos-ref-alt") and queries the
Mutalyzer API to retrieve HGVS genomic (g.), coding (c.), and protein (p.) descriptions.

Returns:
    - transcript HGVS c. notation (if available)
    - protein HGVS p. notation (if available)
    - genomic HGVS g. notation (always provided if valid)
"""

import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any
from pathlib import Path

MUTALYZER_URL = "https://mutalyzer.nl/api/position-converter"


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
# Query Mutalyzer API
# ---------------------------------------------------
def query_mutalyzer(vcf_variant: str, assembly: str = "GRCh38") -> Dict[str, Any]:
    """
    Query Mutalyzer position converter API.

    Args:
        vcf_variant (str): "chrom-pos-ref-alt"
        assembly (str): "GRCh38" (default) or "GRCh37"

    Returns:
        dict with:
            - transcript_c
            - protein_p
            - genomic_g
            - error
            - raw mutalyzer data
    """
    chrom, pos, ref, alt = vcf_variant.split("-")
    pos = int(pos)

    payload = {
        "assembly": assembly,
        "chromosome": chrom,
        "start": pos,
        "end": pos + len(ref) - 1,
        "reference": ref,
        "alternate": alt,
    }

    try:
        r = requests.post(MUTALYZER_URL, json=payload, timeout=15)
        r.raise_for_status()
        data = r.json()
    except Exception as e:
        return {
            "variant": vcf_variant,
            "transcript_c": None,
            "protein_p": None,
            "genomic_g": None,
            "error": str(e),
            "raw": None,
        }

    # Extract genomic HGVS
    genomic_g = data.get("genomicDescription")

    # Extract transcript descriptions (c. + p.)
    tx_list = data.get("transcriptDescriptions", [])
    if tx_list:
        tx = tx_list[0]  # Mutalyzer returns best transcript first
        transcript_c = tx.get("coding")
        protein_p = tx.get("protein")
    else:
        transcript_c = None
        protein_p = None

    return {
        "variant": vcf_variant,
        "transcript_c": transcript_c,
        "protein_p": protein_p,
        "genomic_g": genomic_g,
        "error": None,
        "raw": data,
    }


# ---------------------------------------------------
# Parallel processor
# ---------------------------------------------------
def process_variants_parallel(
    variants: List[str],
    threads: int = 8,
    assembly: str = "GRCh38"
) -> List[Dict[str, Any]]:
    """
    Perform Mutalyzer queries in parallel.

    Returns:
        List of dictionaries with HGVS results.
    """
    results = []

    with ThreadPoolExecutor(max_workers=threads) as executor:
        future_map = {
            executor.submit(query_mutalyzer, v, assembly): v
            for v in variants
        }

        for fut in as_completed(future_map):
            v = future_map[fut]
            try:
                results.append(fut.result())
            except Exception as e:
                results.append({
                    "variant": v,
                    "transcript_c": None,
                    "protein_p": None,
                    "genomic_g": None,
                    "error": str(e),
                    "raw": None,
                })

    return results
