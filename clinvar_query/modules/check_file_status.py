from pathlib import Path
from clinvar_query.modules.parser import parser
from clinvar_query.utils.logger import logger
from clinvar_query.modules.save_function import save_output_to_file

"""Check the file extension and process accordingly.
This will assess the file to see if :
the file is processed or misaligned
the overwrite flag is on or off
This will then output either :
saved_file and status
misaligned file and status
This is then fed to the save_output_to_file module

this will return 
the saved_file, the misaligned_file and the status of the file
"""


def app_file_check(file_path,  processed_folder, error_folder, overwrite=False):

# initialising required variables
    file_end = Path(file_path).suffix.lower()
    title = Path(file_path).stem
    misaligned_title = f"misaligned_{title}"
    saved_file = None
    misaligned_file = None

    try:
        # logic for saving file depending on the conditions
        if file_end == ".csv" or file_end == ".vcf":
            # this assignes the data to the output of the parser
            processed_data, misaligned_data = parser(file_path)
    # if the file is not a csv or vcf then it will
    # output that there is an unsupported file type
    except Exception:
        logger.error("unsupported file type")

    saved_file, status = save_output_to_file(processed_data,
                                                title,
                                                folder=processed_folder,
                                                overwrite=overwrite)

    if misaligned_data:
        misaligned_file, status = save_output_to_file(misaligned_data,
                                                        misaligned_title,
                                                        folder=error_folder,
                                                        overwrite=overwrite)

    return saved_file, misaligned_file, status
