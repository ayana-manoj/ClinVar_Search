#if ClinVar_Search is not found as a module (ModuleNotFoundError), add this project to python path using export PYTHONPATH=/path/to/project/ClinVar_Search:$PYTHONPATH
from ClinVar_Search.logger import logger
from ClinVar_Search.modules.save_function import save_output_to_file
from pathlib import Path
import csv
import re
#These modules read through the csv and vcf file in order to output a consistent sequence
def csvparser(file_path: Path):
    variants = []
    try:
        with open(file_path, newline="") as csvfile:
            csv_file = csv.reader(csvfile, delimiter=",")
            for row in csv_file:
                if not row or row[0].startswith("#"):
                    continue
                if len(row) >=5 :
                    chrom = row[0].strip() 
                    pos = row[1].strip() 
                    ref = row[3].strip() 
                    alt = row[4].strip() 

                if chrom and pos and ref and alt:
                    variant = f"{chrom}-{pos}-{ref}-{alt}"
                    variants.append(variant)
            csv_string = "\n".join(variants)
            return csv_string
        

    except Exception as e:
        logger.error("Failed to parse csv file! {}" .format(e))
        
        return csv_string
""""
The expected inputs and outputs of this could, which parse through, a csv file, would involve 
input:

#CHROM,POS,ID,REF,ALT
17,45983420,.,G,T
output
17-45983420-G-T
"""


def vcfparser(file_path: Path):
    variants = []
    try:
        with open(file_path, newline="") as vcffile:
            vcf_file = csv.reader(vcffile, delimiter="\t")
            for row in vcf_file:
                if not row or row[0].startswith("#"):
                    continue
                if len(row) >=5 :
                    chrom = row[0].strip() 
                    pos = row[1].strip() 
                    ref = row[3].strip() 
                    alt = row[4].strip() 
                #remove "chr prefix" and then move on
                    chrom = chrom.lstrip("chr")

                if chrom and pos and ref and alt:
                    variant = f"{chrom}-{pos}-{ref}-{alt}"
                    variants.append(variant)
            vcf_string = "\n".join(variants)
            return vcf_string


    except Exception as e:
        logger.error ("Failed to parse VCF file!: {}" .format(e))
        
        return vcf_string

""""
The expected inputs and outputs of this could, which parse through, a csv file, would involve 
input:
##fileformat=VCFv4.2				
#CHROM	POS	ID	REF	ALT
19	41970248	.	T	A

output
19-41970248-T-A
"""


 #this function determines a file ending and then makes it so that the correct parser works with it. It needs a file that either ends with csv or vcf           
def determine_file_type(file_path=str):
    try:
        file_path= input(f"which file would you like to read in?")
        #This uses the path library to take the file title without the extension
        title = Path(file_path).stem
        #this evaluates the csv or vcf. If this is neither then an error occurs
        if file_path.endswith(".csv"):
            file_path = csvparser(Fileof)
        elif file_path.endswith(".vcf"):
            file_path = vcfparser(Fileof)
        else:
            logger.error(f"wrong file type! Make sure your file either ends with vcf or csv")
            file_path = None
            file_path = None
    except Exception as e:
            logger.error(f"wrong file type! Make sure your file either ends with vcf or csv")

     
    return file_path, title

"""
The goal now is to further edit the outputs of csvparser and vcfparser so that both outputs are:
Have the same downstream input which will allow for only one stream of modules to work through
This will allow the resulting output to always be compatible with HGVS compliant software which can do downstream analysis
"""


if __name__ == "__main__":
    file_path, title = determine_file_type() 
    save_output_to_file(file_path,title)
                  

