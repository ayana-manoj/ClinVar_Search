import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path


def create_logger():
    #present and parent directory set up, most important
    current_directory = str(Path(__file__).resolve().parent)
    parent_directory = Path(current_directory).parent
    #create logger
    logger = logging.getLogger("ClinVar_Search_logger")
    logger.setLevel(logging.INFO) #This can be changed 

    logger.propagate = False
    if not logger.hasHandlers():
    #making a stream handler, adapted from tutorial
        stream_handler = logging.StreamHandler()
        stream_handler.setLevel(logging.WARNING)
        stream_formatter = logging.Formatter("[%(asctime)s] %(levelname)s %(message)s" )
        stream_handler.setFormatter(stream_formatter)

        #working on rotating file handler
        Path(str(parent_directory)+ "/logs").mkdir(parents=True, exist_ok=True)
        file_handler = RotatingFileHandler(str(parent_directory)+ "/logs/Clinvar_Search.log",
                                        maxBytes=500000,
                                        backupCount=2)
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter("[%(asctime)s] %(levelname)s %(message)s" )
        file_handler.setFormatter(file_formatter)

        #Adding the handlers to logger
        logger.addHandler(stream_handler)
        logger.addHandler(file_handler)
        return logger
    else: 
        return logger

logger = create_logger()