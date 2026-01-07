from clinvar_query.modules.setup_results import create_database
from clinvar_query.utils.logger import logger
import os

"""This module initialises the database
This looks to see if a database file exists
If it doesn't, then it creates a db file
If this doesn't work, a critical error appears
This is because database functionality is essential """

def database_initialise(db_file):
    db_exists = os.path.isfile(db_file)
    try:
        if db_exists:
            return db_file

        else:
            create_database(db_file)
            return db_file
     
    except Exception as e:
        logger.critical("Database searching or creating has failed! "
                        "The app will not have most functionality: {}" .format(e))
