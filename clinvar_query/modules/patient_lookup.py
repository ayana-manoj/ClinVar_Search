import sqlite3
import os
from clinvar_query.utils.logger import logger
from clinvar_query.utils.paths import processed_folder, error_folder
from clinvar_query.utils.paths import database_file

def lookup(latest_results, files, misaligned, database,
           process_folder, err_folder):
    
    try:
        con = sqlite3.connect(database)
        con.row_factory = sqlite3.Row
        cur = con.cursor()

        cur.execute("""
            SELECT * 
            FROM variants
            WHERE date_annotated = (
                SELECT MAX(date_annotated)
                FROM variants
            )
        """)
        latest_results =cur.fetchall()

    except Exception as e:
        logger.error("database error : {}".format(e))
    finally:
        if 'con' in locals():
            con.close()

    # processed patient file lookup
    try:
        if os.path.exists(process_folder):
            files = [file for file in os.listdir(process_folder)
                     if os.path.isfile(os.path.join(process_folder, file))]
            files = sorted(
                files,
                key=lambda file: os.path.getmtime(os.path.join(
                    process_folder, file)),
                reverse=True
            )
    # files with errors in them
        else:
            files = []
        if os.path.exists(err_folder):
            misaligned = [f for f in os.listdir(err_folder)
                          if os.path.isfile(os.path.join(err_folder, f))]
            misaligned = sorted(
                misaligned,
                key=lambda f: os.path.getmtime(os.path.join(err_folder, f)),
                reverse=True
            )
        else:
            misaligned = []
    except Exception as e:
        logger.error("Could not fetch files : {}".format(e))

    return latest_results, files, misaligned