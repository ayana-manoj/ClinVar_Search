import csv
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

def normalize_chrom(chrom):
    """Remove 'chr' prefix if present."""
    return chrom.replace("chr", "").replace("CHR", "")

def query_lovd(vcf_variant):
    """Query LOVD API for a VCF-like variant string."""
    url = f"https://api.lovd.nl/checkHGVS/{requests.utils.quote(vcf_variant, safe='')}"
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        return None, None, {"error": str(e)}

    items = data.get("data", [])
    if not items or "corrected_values" not in items[0]:
        return None, None, data

    corrected = items[0]["corrected_values"]
    best = max(corrected, key=lambda k: corrected[k])
    confidence = corrected[best]
    return best, confidence, data

def process_vcf_parallel(vcf_file, output_csv, threads=8):
    tasks = []
    results = []

    # Read VCF
    with open(vcf_file) as f:
        for line in f:
            if line.startswith("#"):
                continue
            cols = line.strip().split("\t")
            if len(cols) < 5:
                continue

            chrom, pos, _id, ref, alt_field = cols[:5]
            chrom = normalize_chrom(chrom)
            alt_alleles = alt_field.split(",")

            for alt in alt_alleles:
                if alt.startswith("<") or alt == "*":
                    continue  # skip symbolic alleles
                query = f"{chrom}-{pos}-{ref}-{alt}"
                tasks.append((chrom, pos, ref, alt, query))

    print(f"Loaded {len(tasks)} variant alleles for processing with {threads} threads.")

    # Parallel processing
    with ThreadPoolExecutor(max_workers=threads) as executor:
        future_to_variant = {executor.submit(query_lovd, q): (chrom, pos, ref, alt)
                             for chrom, pos, ref, alt, q in tasks}

        for fut in as_completed(future_to_variant):
            chrom, pos, ref, alt = future_to_variant[fut]
            try:
                best_hgvs, conf, raw = fut.result()
            except Exception:
                best_hgvs, conf = None, None

            if best_hgvs is None:
                print(f"⚠ No corrected_values for {chrom}-{pos}-{ref}-{alt}")

            results.append({
                "chrom": chrom,
                "pos": pos,
                "ref": ref,
                "alt": alt,
                "best_hgvs": best_hgvs,
                "confidence": conf
            })

    # Write CSV
    with open(output_csv, "w", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=["chrom", "pos", "ref", "alt", "best_hgvs", "confidence"])
        writer.writeheader()
        writer.writerows(results)

    print(f"\nDone! Output written to {output_csv} ({len(results)} variants processed)")

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Parallel VCF → HGVS converter using LOVD API")
    parser.add_argument("vcf", help="Input VCF file")
    parser.add_argument("out", help="Output CSV file")
    parser.add_argument("--threads", type=int, default=8, help="Number of parallel threads (default 8)")
    args = parser.parse_args()

    process_vcf_parallel(args.vcf, args.out, args.threads)


