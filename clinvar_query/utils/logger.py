import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from clinvar_query.utils.paths import logs_folder


def create_logger():
    # present and parent directory set up, most important
    # create logger
    logger = logging.getLogger("ClinVar_Search_logger")
    logger.setLevel(logging.INFO)

    logger.propagate = False
    if not logger.hasHandlers():

        stream_handler = logging.StreamHandler()
        stream_handler.setLevel(logging.WARNING)
        stream_formatter = logging.Formatter("[%(asctime)s]"
                                             "%(levelname)s %(message)s")
        stream_handler.setFormatter(stream_formatter)

        # working on rotating file handler
        Path(str(logs_folder)).mkdir(parents=True,
                                                    exist_ok=True)
        file_handler = RotatingFileHandler(str(logs_folder) +
                                           "/Clinvar_Search.log",
                                           maxBytes=500000,
                                           backupCount=2)
        file_handler.setLevel(logging.INFO)
        file_formatter = logging.Formatter("[%(asctime)s]"
                                           "%(levelname)s %(message)s")
        file_handler.setFormatter(file_formatter)

        # Adding the handlers to logger
        logger.addHandler(stream_handler)
        logger.addHandler(file_handler)
        return logger
    else:
        return logger


logger = create_logger()
