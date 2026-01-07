import sqlite3
import os
from clinvar_query.utils.logger import logger
from clinvar_query.utils.paths import processed_folder, error_folder
from clinvar_query.utils.paths import database_file

"""
The lookup module uses a sql query to output patient results in the results page
This uses left join to combine variants and clinvar data
and is sorted by the latest date to ensure only 1 patient is used
this is fed in latest_results to output
patient id, variant id, consensus classification, star rating, date annotated

The file lookup section validates the existence of:
processed file folder
misaligned file folder

This is then sorted by date

"""
#debugged with chatGPT

def lookup(latest_results, files, misaligned, database,
           process_folder, err_folder):
    
    try:
        con = sqlite3.connect(database)
        con.row_factory = sqlite3.Row
        cur = con.cursor()

        cur.execute("""
            SELECT
                variants.patient_id,
                variants.variant_id,
                clinvar.consensus_classification,
                clinvar.star_rating,
                clinvar.allele_frequency,
                variants.date_annotated
            FROM variants
            LEFT JOIN clinvar
                ON variants.variant_id = clinvar.variant_id
            WHERE variants.date_annotated = (
                SELECT MAX(date_annotated) FROM variants)      
        """)
        latest_results =cur.fetchall()

    except Exception as e:
        logger.error("database error : {}".format(e))
    finally:
        if 'con' in locals():
            con.close()

    # processed patient file lookup made with chatGPT
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
    # files with errors in them made with chatGPT
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