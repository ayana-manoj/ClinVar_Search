
from clinvar_query.logger import logger
from pathlib import Path
import csv


def parser(file_path):
    """This module parses through the uploaded file
it first checks if it ends in csv or vcf
then it extracts the data
Example input
12,40294866,.,G,T
Example output
12-40294866-G-T
"""
    variants = []
    misaligned_rows = []
    try:
        file_end = Path(file_path).suffix
        if file_end == ".csv":
            delimiter = ","
        elif file_end == ".vcf":
            delimiter = "\t"
        else:
            logger.error("Not csv or vcf! Check again")
        with open(file_path, newline="") as parsefile:
            parse_file = csv.reader(parsefile, delimiter=delimiter)
            for row in parse_file:
                if not row or row[0].startswith("#"):
                    continue

                chrom = pos = ref = alt = None

                if len(row) >= 5:
                    chrom = row[0].strip()
                    pos = row[1].strip()
                    ref = row[3].strip()
                    alt = row[4].strip()
                # remove "chr prefix" and then move on
                    chrom = chrom.lstrip("chr")

                if chrom and pos and ref and alt:
                    variant = f"{chrom}-{pos}-{ref}-{alt}"
                    variants.append(variant)
                else:
                    misaligned_row = f"incomplete or misaligned row {row}"
                    misaligned_rows.append(misaligned_row)
                    logger.error = (f"incomplete or misaligned row {row}")

            parse_string = "\n".join(variants)
            if misaligned_rows:
                misaligned_string = "\n".join(misaligned_rows)
                return parse_string, misaligned_string
            else:
                misaligned_string = ""
                return parse_string, misaligned_string
    except Exception as e:
        logger.error("Failed to parse csv/vcf file! {}" .format(e))
        return None, None
