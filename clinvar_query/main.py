"""
main.py
------------------------
Pipeline:
    1. Read variants from TXT file
    2. Query VariantValidator → get MANE or fallback HGVS c.
    3. Query ClinVar using the HGVS c.
    4. Output combined structured results

Requires:
    - variantvalidator_hgvs_query.py
    - clinvar_api_query.py
"""

from pathlib import Path
from diskcache import Cache

from clinvar_query.modules.variantvalidator_hgvs_query import (
    read_variants_from_txt,
    process_variants_parallel
)

from clinvar_query.modules.clivar_api_query import query_clinvar_by_hgvs_c


# -----------------------------------------------------
# Paths
# -----------------------------------------------------
BASE_DIR = Path(__file__).parent
INPUT_FILE = BASE_DIR / "modules" / "Clinvar_Search_Output_Files" / "Patient1.txt"

CACHE_DIR = BASE_DIR / "modules" / "cache"
CACHE_DIR.mkdir(exist_ok=True)
clinvar_cache = Cache(CACHE_DIR)


# -----------------------------------------------------
# Main pipeline
# -----------------------------------------------------
def main() -> list[dict]:
    print("🚀 Starting ClinVar Search Pipeline...")
    print(f"📄 Reading input variants from: {INPUT_FILE}")

    # 1️⃣ Load variants
    variants = read_variants_from_txt(INPUT_FILE)
    if not variants:
        print("❌ No valid variants found.")
        return []

    # 2️⃣ Query VariantValidator (parallel)
    print("\n🔎 Querying VariantValidator for HGVS mapping...")
    vv_results = process_variants_parallel(variants)

    final_results = []

    # 3️⃣ Query ClinVar for each HGVS c. (MANE preferred)
    print("\n🧬 Querying ClinVar...")

    for entry in vv_results:

        print("\n-----------------------------------------------------")
        print(f"➡ Variant {entry.get('variant')}")

        # Prefer MANE transcript HGVS c.
        if entry.get("mane_select_available"):
            hgvs_c = entry.get("mane_hgvs_c")
            print(f"   MANE Select transcript found: {entry.get('mane_transcript')}")
            print(f"   Using MANE HGVS c.: {hgvs_c}")
        else:
            hgvs_c = entry.get("top_hgvs_c")
            print("   ❌ No MANE Select transcript available")
            print(f"   Using top transcript: {entry.get('top_transcript')}")
            print(f"   HGVS c.: {hgvs_c}")

        # Gene data
        gene_symbol = entry.get("gene_symbol")
        gene_name = entry.get("gene_name")
        hgnc_id = entry.get("hgnc_id")
        print(f"   Gene: {gene_symbol} ({gene_name}), HGNC:{hgnc_id}")

        # ---------------------------------------------------
        # ClinVar lookup
        # ---------------------------------------------------
        if not hgvs_c:
            print("   ❌ No HGVS c. notation → skipping ClinVar query.")
            clinvar_data = None
        else:
            if hgvs_c in clinvar_cache:
                print("   🔁 Using cached ClinVar result")
                clinvar_data = clinvar_cache[hgvs_c]
            else:
                print("   🌐 Querying ClinVar API...")
                clinvar_data = query_clinvar_by_hgvs_c(hgvs_c)
                clinvar_cache[hgvs_c] = clinvar_data

        # ---------------------------------------------------
        # Collect combined output
        # ---------------------------------------------------
        final_results.append({
            "input_variant": entry.get("variant"),

            # HGVS choices
            "mane_selected": entry.get("mane_select_available"),
            "mane_transcript": entry.get("mane_transcript"),
            "mane_hgvs_c": entry.get("mane_hgvs_c"),
            "fallback_transcript": entry.get("top_transcript"),
            "fallback_hgvs_c": entry.get("top_hgvs_c"),

            # Gene info
            "gene_symbol": gene_symbol,
            "gene_name": gene_name,
            "hgnc_id": hgnc_id,

            # ClinVar
            "clinvar": clinvar_data,
        })

    print("\n🎉 Pipeline complete!")
    return final_results


# -----------------------------------------------------
# Run script directly
# -----------------------------------------------------
if __name__ == "__main__":
    results = main()

    print("\n===== Final Combined Results =====")
    for r in results:
        print(r)



#
