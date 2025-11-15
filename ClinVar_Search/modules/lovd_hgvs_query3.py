import csv
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
import os
from pathlib import Path
from typing import List, Tuple, Dict, Any, Optional
from ClinVar_Search.logger import logger  # Custom logger module


# -------------------------
# Configuration
# -------------------------
INPUT_TXT_FILE: str = "ClinVar_Search/modules/Clinvar_Search_Output_Files/Patient1.txt"
OUTPUT_CSV_FILE: str = "ClinVar_Search/modules/lovd_hgvs_query/patient1.csv"
THREADS: int = 8  # Number of parallel LOVD API requests


# -------------------------
# LOVD API Query Function
# -------------------------
def query_lovd(vcf_variant: str) -> Tuple[Optional[str], Optional[float], Dict[str, Any]]:
    """
    Query the LOVD API to check a VCF-like variant string.

    Args:
        vcf_variant (str): Variant in the format "chrom-pos-ref-alt" (e.g., "17-45983420-G-T").

    Returns:
        Tuple containing:
            best_hgvs (Optional[str]): HGVS-formatted variant with highest confidence.
            confidence (Optional[float]): Confidence score of the HGVS suggestion.
            data (dict): Raw JSON response from LOVD API.
    """
    url: str = f"https://api.lovd.nl/checkHGVS/{requests.utils.quote(vcf_variant, safe='')}"

    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        data: Dict[str, Any] = resp.json()
    except Exception as e:
        logger.error(f"API request failed for {vcf_variant}: {e}")
        return None, None, {"error": str(e)}

    items: List[Dict[str, Any]] = data.get("data", [])
    if not items or "corrected_values" not in items[0]:
        logger.warning(f"No corrected_values returned for {vcf_variant}")
        return None, None, data

    corrected: Dict[str, float] = items[0]["corrected_values"]
    best: str = max(corrected, key=lambda k: corrected[k])
    confidence: float = corrected[best]

    return best, confidence, data


# -------------------------
# Read TXT Variants
# -------------------------
def read_variants_from_txt(txt_file: str) -> List[Tuple[str, str, str, str, str]]:
    """
    Read variants from a TXT file and validate format.

    Each line should be in "chrom-pos-ref-alt" format, e.g., "17-45983420-G-T".

    Args:
        txt_file (str): Path to the input TXT file.

    Returns:
        List of tuples: Each tuple contains (chrom, pos, ref, alt, original_variant).
    """
    tasks: List[Tuple[str, str, str, str, str]] = []

    with open(txt_file) as f:
        for line in f:
            variant: str = line.strip()
            if not variant or variant.startswith("#"):
                continue

            parts: List[str] = variant.split("-")
            if len(parts) != 4:
                logger.warning(f"Skipping invalid line: {variant}")
                continue

            chrom, pos, ref, alt = parts
            tasks.append((chrom, pos, ref, alt, variant))

    logger.info(f"Loaded {len(tasks)} valid variants from {txt_file}")
    return tasks


# -------------------------
# Parallel Processing
# -------------------------
def process_variants_parallel(tasks: List[Tuple[str, str, str, str, str]],
                              output_csv: str,
                              threads: int = 8) -> None:
    """
    Process a list of variants in parallel using LOVD API.

    Args:
        tasks (List[Tuple[str, str, str, str, str]]): Output from read_variants_from_txt().
        output_csv (str): Path to output CSV file.
        threads (int): Number of parallel threads for API requests.

    Returns:
        None
    """
    results: List[Dict[str, Any]] = []
    logger.info(f"Processing {len(tasks)} variants with {threads} threads...")

    # Use ThreadPoolExecutor for parallel API calls
    with ThreadPoolExecutor(max_workers=threads) as executor:
        future_to_variant: Dict[Any, Tuple[str, str, str, str]] = {
            executor.submit(query_lovd, q): (chrom, pos, ref, alt)
            for chrom, pos, ref, alt, q in tasks
        }

        for fut in as_completed(future_to_variant):
            chrom, pos, ref, alt = future_to_variant[fut]
            try:
                best_hgvs, conf, raw = fut.result()
            except Exception as e:
                logger.error(f"Error processing {chrom}-{pos}-{ref}-{alt}: {e}")
                best_hgvs, conf = None, None

            if best_hgvs is None:
                logger.warning(f"No best HGVS for {chrom}-{pos}-{ref}-{alt}")

            results.append({
                "chrom": chrom,
                "pos": pos,
                "ref": ref,
                "alt": alt,
                "best_hgvs": best_hgvs,
                "confidence": conf
            })

    # Ensure output directory exists
    output_dir: str = os.path.dirname(output_csv)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
        logger.info(f"Created output directory: {output_dir}")

    # Write results to CSV
    with open(output_csv, "w", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=["chrom", "pos", "ref", "alt", "best_hgvs", "confidence"])
        writer.writeheader()
        writer.writerows(results)

    logger.info(f"Done! Output written to {output_csv} ({len(results)} variants processed)")


# -------------------------
# Main Function
# -------------------------
def main() -> None:
    """
    Main entry point for the script.

    1. Reads variants from a fixed TXT file.
    2. Processes them in parallel via LOVD API.
    3. Outputs results to a CSV file.
    """
    tasks: List[Tuple[str, str, str, str, str]] = read_variants_from_txt(INPUT_TXT_FILE)
    if not tasks:
        logger.warning("No valid variants to process.")
        return

    process_variants_parallel(tasks, OUTPUT_CSV_FILE, THREADS)


# Run the script
if __name__ == "__main__":
    main()




