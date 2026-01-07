from clinvar_query.utils.paths import processed_folder
from clinvar_query.utils.logger import logger
import os

"""
This saves the processed data from the parser module 
This is saved in a specified directory and is depen

If the file already exists in the output directory,
then the user can decide what happens
an error will occur on the terminal and is logged
To communicate to the end user what is going on,
there are several flags which are used in error handling

these are:
created = where a file is created
overwritten = where a file has been overwritten
skipped = where a file has not been overwritten
error = where there has been an error
"""

def save_output_to_file(content, title, folder=processed_folder,
                        overwrite=False):

    """Saves the processed content to the processed folder."""
    os.makedirs(folder, exist_ok=True)
    output_path = os.path.join(folder, f"{title}_processed.txt")

# first evaluate if file exists
    file_exists = os.path.isfile(output_path)

    try:
        if file_exists and not overwrite:
            logger.warning(f"{output_path} "
                           "already exists and overwrite is False")
            return None, "skipped"
        status = "overwritten" if file_exists else "created"
    except Exception as e:
        logger.error(f"Error writing to {output_path} : {str(e)}")

    try:
        with open(output_path, 'w') as f:
            f.write(content)
        return output_path, status
    except Exception as e:
        logger.error(f"Error writing to {output_path} : {str(e)}")
        return None, "error"
