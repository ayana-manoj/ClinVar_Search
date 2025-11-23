"""
variantvalidator_hgvs_query.py
--------------------------------
Query VariantValidator API to obtain:

    - MANE Select transcript (if present)
    - HGVS c. notation
    - Gene symbol
    - Gene name
    - HGNC ID

If MANE Select is not available, the script:
    - Reports this
    - Falls back to the top transcript returned by VariantValidator

Input variant format (from TXT file):
    chrom-pos-ref-alt
"""

import requests
from pathlib import Path
from typing import List, Dict, Any


# ============================================================
# Load variants from TXT
# ============================================================
def read_variants_from_txt(txt_file: str | Path) -> List[str]:
    """
    Load variants formatted as:
        chrom-pos-ref-alt
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
                print(f"⚠️ Skipping invalid variant line: {variant}")
                continue

            variants.append(variant)

    print(f"📌 Loaded {len(variants)} variants from {txt_file}")
    return variants


# ============================================================
# Query VariantValidator API
# ============================================================
VV_BASE = "https://rest.variantvalidator.org/VariantValidator/variantvalidator"


def query_variantvalidator(vcf_variant: str, assembly: str = "hg38") -> Dict[str, Any]:
    """
    Query VariantValidator using genomic coordinates
    and extract MANE transcripts when available.

    Args:
        vcf_variant: "chrom-pos-ref-alt"

    Returns:
        {
            "variant": ...,
            "mane_select_available": True/False,
            "mane_transcript": str | None,
            "mane_hgvs_c": str | None,
            "top_transcript": str,
            "top_hgvs_c": str,
            "gene_symbol": str,
            "gene_name": str,
            "hgnc_id": str,
            "raw": raw_json_response
        }
    """

    chrom, pos, ref, alt = vcf_variant.split("-")

    # Required VariantValidator format: chr:posREF>ALT
    vv_variant = f"{chrom}:{pos}{ref}>{alt}"
    url = f"{VV_BASE}/{assembly}/{vv_variant}?content-type=application/json"

    try:
        r = requests.get(url, timeout=20)
        r.raise_for_status()
        data = r.json()
    except Exception as e:
        return {
            "variant": vcf_variant,
            "error": str(e),
            "mane_select_available": False,
            "mane_transcript": None,
            "mane_hgvs_c": None,
            "top_transcript": None,
            "top_hgvs_c": None,
            "gene_symbol": None,
            "gene_name": None,
            "hgnc_id": None,
            "raw": None
        }

    # -------------------------------
    # Extract transcripts
    # -------------------------------
    tx_list = data.get("transcripts", [])
    if not tx_list:
        return {
            "variant": vcf_variant,
            "error": "No transcripts returned",
            "mane_select_available": False,
            "mane_transcript": None,
            "mane_hgvs_c": None,
            "top_transcript": None,
            "top_hgvs_c": None,
            "gene_symbol": None,
            "gene_name": None,
            "hgnc_id": None,
            "raw": data
        }

    # -------------------------------
    # Look for MANE Select
    # -------------------------------
    mane_tx = None
    for t in tx_list:
        if t.get("mane_status", "").lower() == "mane select":
            mane_tx = t
            break

    # -------------------------------
    # Fallback: top transcript = first returned
    # -------------------------------
    top_tx = tx_list[0]

    # Extract gene
    gene_info = data.get("gene", {})
    gene_symbol = gene_info.get("symbol")
    gene_name = gene_info.get("name")
    hgnc_id = gene_info.get("hgnc_id")

    # ------------------------------------------------------------
    # MANE Select found
    # ------------------------------------------------------------
    if mane_tx:
        return {
            "variant": vcf_variant,
            "mane_select_available": True,
            "mane_transcript": mane_tx.get("transcript"),
            "mane_hgvs_c": mane_tx.get("hgvs_c"),
            "top_transcript": top_tx.get("transcript"),
            "top_hgvs_c": top_tx.get("hgvs_c"),
            "gene_symbol": gene_symbol,
            "gene_name": gene_name,
            "hgnc_id": hgnc_id,
            "raw": data
        }

    # ------------------------------------------------------------
    # No MANE Select → return top transcript
    # ------------------------------------------------------------
    return {
        "variant": vcf_variant,
        "mane_select_available": False,
        "mane_transcript": None,
        "mane_hgvs_c": None,
        "top_transcript": top_tx.get("transcript"),
        "top_hgvs_c": top_tx.get("hgvs_c"),
        "gene_symbol": gene_symbol,
        "gene_name": gene_name,
        "hgnc_id": hgnc_id,
        "raw": data
    }


# ============================================================
# Parallel runner
# ============================================================
from concurrent.futures import ThreadPoolExecutor, as_completed


def process_variants_parallel(variants: List[str], threads: int = 8) -> List[Dict[str, Any]]:
    """Process all VariantValidator requests in parallel."""
    results = []

    with ThreadPoolExecutor(max_workers=threads) as ex:
        future_map = {ex.submit(query_variantvalidator, v): v for v in variants}

        for fut in as_completed(future_map):
            v = future_map[fut]
            try:
                results.append(fut.result())
            except Exception as e:
                results.append({
                    "variant": v,
                    "error": str(e),
                    "mane_select_available": False,
                    "mane_transcript": None,
                    "mane_hgvs_c": None,
                    "top_transcript": None,
                    "top_hgvs_c": None,
                    "gene_symbol": None,
                    "gene_name": None,
                    "hgnc_id": None,
                    "raw": None
                })

    return results
