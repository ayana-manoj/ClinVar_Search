import sqlite3
import os
from clinvar_query.logger import logger
from clinvar_query.utils.paths import processed_folder, error_folder
from clinvar_query.utils.paths import database_file

def lookup(latest_results, files, misaligned):
    try:
        con = sqlite3.connect(database_file)
        con.row_factory = sqlite3.Row
        cur = con.cursor()

        cur.execute("SELECT * FROM annotated_results"
                    " ORDER BY date_annotated DESC LIMIT 1")
        latest_results = cur.fetchone()

    except Exception as e:
        logger.error("database error : {}".format(e))
    finally:
        if 'con' in locals():
            con.close()

    # processed patient file lookup
    try:
        if os.path.exists(processed_folder):
            files = [file for file in os.listdir(processed_folder)
                     if os.path.isfile(os.path.join(processed_folder, file))]
            files = sorted(
                files,
                key=lambda file: os.path.getmtime(os.path.join(
                    processed_folder, file)),
                reverse=True
            )
    # files with errors in them
        else:
            files = []
        if os.path.exists(error_folder):
            misaligned = [f for f in os.listdir(error_folder)
                          if os.path.isfile(os.path.join(error_folder, f))]
            misaligned = sorted(
                misaligned,
                key=lambda f: os.path.getmtime(os.path.join(error_folder, f)),
                reverse=True
            )
        else:
            misaligned = []
    except Exception as e:
        logger.error("Could not fetch files : {}".format(e))

    return latest_results, files, misaligned