import os
from flask import request
from clinvar_query.utils.logger import logger

"""This is used to read uploads
This looks for files and reads the file
There is error handling involved

If there is a done file:
File is read

If there is no file:
No file selected will pop up

If there is a file but no file path:
Please refresh and try again message pops up

"""

def read_file(folder, filetype):
    try:
        done_file = request.args.get(filetype)
        if not done_file:
            return "No file selected!", 400

        file_path = os.path.join(folder, done_file)
        if not os.path.exists(file_path):
            return "File not found, please refresh and try again."
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        logger.error("Reading processed or misaligned files has failed : {}".format(e))
    return content
