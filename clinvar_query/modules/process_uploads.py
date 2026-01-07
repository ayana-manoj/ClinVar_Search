from werkzeug.utils import secure_filename
from clinvar_query.modules.check_file_status import app_file_check
from clinvar_query.utils.logger import logger
import os

"""This module evaluates the state of
processed file
status
to return a dictionary of values, this dictionary contains
the redirect endpoint, the message parameters
This will then take inputs from messages.py to output informative data
This is fed into upload.py

"""


def process_upload_file(file, folder, processed_folder, error_folder,  overwrite=False):
    # This does not have try except blocks as the logic here
    # involves redirecting to an error site.
    # However, there are  still loggers with levels to ensure it is informative
    #parts of this function were made with chatGPT
    if not file:
        return {"redirect_endpoint": "error_site", "messages": {"message":
                                                                "no_file"}}

    filename = secure_filename(file.filename)
    upload_path = os.path.join(folder, filename)
    # save the file
    file.save(upload_path)

    # call files

    processed_file, misaligned_file, status = app_file_check(
                                                upload_path,
                                                processed_folder,
                                                error_folder,
                                                overwrite=overwrite)

    # look for redirecting now
    if not processed_file and status != "skipped":
        logger.error("unsupported file type")
        return {"redirect_endpoint": "process.error_site",
                "message_params": {"message": "unsupported_file",
                                   "file": file.filename}}

    if not processed_file and status == "skipped":

        return {"redirect_endpoint": "process.error_site",
                "message_params": {"message": "skipped", "file": file.filename}}

    if processed_file and misaligned_file:
        if status == "created":

            logger.warning(f"{filename} file was processed, but is misaligned")
            return {"redirect_endpoint": "process.upload_success",
                    "message_params": {"message": "misaligned_created",
                                         "file": file.filename}}
        
        elif status == "overwritten":
            logger.warning(f"{filename} was misaligned and overwritten")
            return {"redirect_endpoint": "process.upload_success",
                    "message_params": {"message": "misaligned_overwritten",
                                         "file": file.filename}}

    if processed_file and not misaligned_file:
        if status == "created":
            return {"redirect_endpoint": "process.upload_success",
                    "message_params": {"message": "upload_success",
                                         "file": file.filename}}

        elif status == "overwritten":
            logger.warning(f"{filename} Has been overwritten successfully")
            return {"redirect_endpoint": "process.upload_success",
                    "message_params": {"message": "overwritten_success",
                                         "file": file.filename}}
            
