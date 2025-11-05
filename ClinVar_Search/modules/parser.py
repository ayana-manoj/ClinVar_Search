#if ClinVar_Search is not found as a module (ModuleNotFoundError), add this project to python path using export PYTHONPATH=/path/to/project/ClinVar_Search:$PYTHONPATH
from ClinVar_Search.logger import logger
from ClinVar_Search.modules.save_function import save_output_to_file
from pathlib import Path
import csv
import re
#These modules read through the csv and vcf file in order to output a consistent sequence
def csvparser(Fileof):
    try:
        csv_object = ""
        with open (Fileof, newline="") as csvfile:
            csvparser = csv.reader(csvfile, delimiter=" ", quotechar= "|")
            for row in csvparser:
                csv_object +=("\n"+" ".join(row))
                csv_object = re.sub(r"^#.*","", csv_object, flags=re.MULTILINE)
                csv_object = csv_object.replace(".", "")
                csv_object = csv_object.replace(",", "-")
                csv_object = csv_object.replace("--", "-")
                csv_object = csv_object.strip()      
        Fileof = csv_object
    except Exception as e:
        logger.error("Failed to parse csv file! {}" .format(e))
        
    return Fileof
""""
The expected inputs and outputs of this could, which parse through, a csv file, would involve 
input:

#CHROM,POS,ID,REF,ALT
17,45983420,.,G,T
output
17-45983420-G-T
"""


def vcfparser(Fileof):
    try:
        vcf_object = ""
        with open (Fileof, newline="") as vcffile:
            vcfparser = csv.reader(vcffile, delimiter="\t", quotechar= "|")
            for row in vcfparser:
                vcf_object +=("\n"+" ".join(row))
                vcf_object = re.sub(r"^#.*","", vcf_object, flags=re.MULTILINE)
                vcf_object = vcf_object.replace(".", "")
                vcf_object = vcf_object.replace(" ", "-")
                vcf_object = vcf_object.replace("--", "-")
                vcf_object = vcf_object.strip()
        Fileof = vcf_object
    except Exception as e:
        logger.error ("Failed to parse VCF file!: {}" .format(e))
        
    return Fileof

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
def determine_file_type():
    try:
        Fileof= input(f"which file would you like to read in?")
        #This uses the path library to take the file title without the extension
        title = Path(Fileof).stem
        #this evaluates the csv or vcf. If this is neither then an error occurs
        if Fileof.endswith(".csv"):
            Fileof = csvparser(Fileof)
        elif Fileof.endswith(".vcf"):
            Fileof = vcfparser(Fileof)
        else:
            logger.error(f"wrong file type! Make sure your file either ends with vcf or csv")
            Fileof = None
            title = None
    except Exception as e:
            logger.error(f"wrong file type! Make sure your file either ends with vcf or csv")

     
    return Fileof, title

"""
The goal now is to further edit the outputs of csvparser and vcfparser so that both outputs are:
Have the same downstream input which will allow for only one stream of modules to work through
This will allow the resulting output to always be compatible with HGVS compliant software which can do downstream analysis
"""


if __name__ == "__main__":
    Fileof, title = determine_file_type() 
    save_output_to_file(Fileof,title)
                  

