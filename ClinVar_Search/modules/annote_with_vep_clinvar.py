#!/usr/bin/env python3
"""
annotate_with_vep_clinvar_mane.py
Annotate a VCF file using Ensembl VEP + ClinVar + MANE transcript.

This script:
- Runs Ensembl VEP on a VCF file
- Adds ClinVar plugin fields (clinical significance, review status/stars)
- Includes MANE Select/Plus Clinical transcript annotations
- Outputs a clean TSV file

Usage:
    python annotate_with_vep_clinvar_mane.py \
        --input variants.vcf \
        --output annotated_variants.tsv \
        --assembly GRCh38
"""

import argparse
import os
import subprocess
import sys


def run_vep(input_vcf, output_file, assembly):
    """
    Run Ensembl VEP with ClinVar and MANE Select plugin.
    """
    # Check that VEP is available
    try:
        subprocess.run(["vep", "--help"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except FileNotFoundError:
        sys.exit("❌ Error: 'vep' command not found. Please install Ensembl VEP first.")

    # Path to local cache (modify if needed)
    cache_dir = os.path.expanduser("~/.vep")

    # Define the fields you want in the final output
    # Including MANE transcript and ClinVar review status (stars)
    fields = ",".join([
        "Uploaded_variation",
        "Location",
        "SYMBOL",
        "Gene",
        "MANE_SELECT",
        "MANE_PLUS_CLINICAL",
        "HGVSc",
        "HGVSp",
        "Consequence",
        "CLIN_SIG",
        "CLIN_SIG_CONF",
        "CLIN_SIG_TRAIT",
        "CLIN_SIG_REVIEW_STATUS",   # Contains the review status (used for star rating)
        "ClinVar"
    ])

    # Build VEP command
    cmd = [
        "vep",
        "-i", input_vcf,
        "-o", output_file,
        "--cache",
        "--assembly", assembly,
        "--dir_cache", cache_dir,
        "--symbol",
        "--hgvs",
        "--mane",                  # Add MANE Select/Plus Clinical transcripts
        "--plugin", "ClinVar",     # Add ClinVar data (requires cache)
        "--tab",
        "--fields", fields,
        "--force_overwrite"
    ]

    print(f"🚀 Running VEP with ClinVar and MANE transcript annotation on {input_vcf} ...")
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        print("❌ VEP failed with error:")
        print(result.stderr)
        sys.exit(1)
    else:
        print(f"✅ Annotation complete! Results saved to {output_file}")


def add_star_rating(tsv_file):
    """
    Post-process the output TSV to add a 'ClinVar_Stars' column
    based on the review status text.
    """
    import pandas as pd

    print("⭐ Adding ClinVar star rating based on review status...")

    df = pd.read_csv(tsv_file, sep="\t", comment="#")

    # Define mapping from review status to star rating
    star_map = {
        "practice guideline": 4,
        "reviewed by expert panel": 3,
        "criteria provided, multiple submitters, no conflicts": 2,
        "criteria provided, conflicting interpretations": 1,
        "criteria provided, single submitter": 1,
        "no assertion criteria provided": 0,
        "no assertion provided": 0,
        "no assertion for the individual variant": 0
    }

    def get_stars(status):
        if isinstance(status, str):
            for key, val in star_map.items():
                if key in status.lower():
                    return val
        return 0

    df["ClinVar_Stars"] = df["CLIN_SIG_REVIEW_STATUS"].apply(get_stars)
    df.to_csv(tsv_file, sep="\t", index=False)

    print(f"✅ Added ClinVar star ratings to {tsv_file}")


def main():
    parser = argparse.ArgumentParser(description="Annotate VCF with ClinVar and MANE transcript using Ensembl VEP.")
    parser.add_argument("--input", required=True, help="Input VCF file")
    parser.add_argument("--output", required=True, help="Output annotated TSV file")
    parser.add_argument("--assembly", default="GRCh38", choices=["GRCh37", "GRCh38"],
                        help="Genome assembly version (default: GRCh38)")
    args = parser.parse_args()

    run_vep(args.input, args.output, args.assembly)
    add_star_rating(args.output)


if __name__ == "__main__":
    main()
