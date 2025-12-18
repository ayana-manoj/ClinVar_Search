import os
from flask import request
from clinvar_query.utils.logger import logger


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
