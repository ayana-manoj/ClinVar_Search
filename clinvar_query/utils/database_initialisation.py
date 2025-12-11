from clinvar_query.modules.setup_results import create_database
from clinvar_query.logger import logger
import os


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
